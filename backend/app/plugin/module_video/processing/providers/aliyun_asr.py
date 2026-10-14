from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import oss2

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from ..asr_contract import (
    SpeechRecognitionResult,
    SpeechRecognitionTaskResult,
    SpeechUtterance,
    SpeechWord,
)


class AliyunDashScopeAsrProvider:
    """阿里百炼非实时 ASR provider。"""

    provider_name = "aliyun_dashscope_asr"
    _engine_name = "qwen3-filetrans-word-timestamps"
    _submit_path = "/api/v1/services/audio/asr/transcription"
    _task_path_prefix = "/api/v1/tasks"
    _request_timeout_seconds = 180.0
    _poll_interval_seconds = 5.0
    _query_deadline_seconds = 1800.0

    def __init__(self) -> None:
        self._validate_settings()
        self._oss_bucket = self._build_oss_bucket()

    async def transcribe_audio(
        self,
        *,
        source_path: Path,
        file_name: str,
        task_no: str,
    ) -> SpeechRecognitionTaskResult:
        """上传本地音频到阿里 OSS，并发起百炼异步转写。"""
        if not source_path.exists():
            raise CustomException(msg=f"阿里 ASR 源音频不存在: {source_path}")

        object_key = self._build_object_key(file_name)
        await asyncio.to_thread(
            self._oss_bucket.put_object_from_file,
            object_key,
            str(source_path),
        )
        source_audio_url = self._sign_object_url(object_key)

        try:
            submit_response = await self._submit_transcription_task(
                task_no=task_no,
                source_audio_url=source_audio_url,
            )
            task_id = self._extract_task_id(submit_response)
            request_id = self._request_id_from_response(submit_response)
            log.info(
                "阿里百炼 ASR 任务已提交: "
                f"task_no={task_no}, task_id={task_id}, request_id={request_id or 'unknown'}"
            )

            task_response = await self._wait_for_task(task_id)
            transcription_url = self._extract_transcription_url(task_response)
            transcription_payload = await self._fetch_transcription_payload(transcription_url)
            recognition_result = self._parse_transcription_payload(
                payload=transcription_payload,
                task_id=task_id,
                request_id=request_id or task_id,
                log_id=self._request_id_from_response(task_response),
                transcription_url=transcription_url,
            )
            log.info(
                "阿里百炼 ASR 结果解析完成: "
                f"task_id={task_id}, model={recognition_result.model}, "
                f"utterance_count={len(recognition_result.utterances)}, "
                f"word_count={recognition_result.word_count}"
            )
            return SpeechRecognitionTaskResult(
                source_audio_object_key=object_key,
                source_audio_url=source_audio_url,
                recognition_result=recognition_result,
            )
        finally:
            try:
                await asyncio.to_thread(self._oss_bucket.delete_object, object_key)
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "阿里 ASR 临时音频清理失败: "
                    f"object_key={object_key}, error={exc!s}"
                )

    async def _submit_transcription_task(
        self,
        *,
        task_no: str,
        source_audio_url: str,
    ) -> httpx.Response:
        """提交阿里百炼异步音频转写任务。"""
        model = settings.ALIYUN_DASHSCOPE_ASR_MODEL
        if model == "qwen-audio-3.0-asr-flash-filetrans":
            input_payload = {
                "file_urls": [source_audio_url],
            }
            parameters = {
                "language_hints": [settings.ALIYUN_DASHSCOPE_ASR_LANGUAGE],
                "enable_itn": settings.ALIYUN_DASHSCOPE_ASR_ENABLE_ITN,
            }
        else:
            input_payload = {
                "file_url": source_audio_url,
            }
            parameters = {
                "language": settings.ALIYUN_DASHSCOPE_ASR_LANGUAGE,
                "enable_itn": settings.ALIYUN_DASHSCOPE_ASR_ENABLE_ITN,
                "enable_words": True,
            }
        payload = {
            "model": model,
            "input": input_payload,
            "parameters": parameters,
        }
        return await self._request_json(
            method="POST",
            path=self._submit_path,
            headers={
                "Authorization": f"Bearer {settings.ALIYUN_DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
                "X-DashScope-Uid": task_no,
            },
            json_body=payload,
        )

    async def _wait_for_task(self, task_id: str) -> httpx.Response:
        """轮询阿里百炼异步任务，直到完成。"""
        deadline = time.monotonic() + self._query_deadline_seconds
        while time.monotonic() < deadline:
            response = await self._request_json(
                method="GET",
                path=f"{self._task_path_prefix}/{task_id}",
                headers={
                    "Authorization": f"Bearer {settings.ALIYUN_DASHSCOPE_API_KEY}",
                },
            )
            status = self._extract_task_status(response).upper()
            if status in {"SUCCEEDED", "SUCCESS"}:
                return response
            if status in {"FAILED", "FAILURE", "CANCELED", "CANCELLED"}:
                raise CustomException(
                    msg=(
                        "阿里百炼 ASR 任务失败: "
                        f"task_id={task_id}, status={status}, "
                        f"error={self._extract_task_error_message(response)}"
                    )
                )
            if status not in {"PENDING", "RUNNING", "QUEUED"}:
                raise CustomException(
                    msg=f"阿里百炼 ASR 返回未知任务状态: task_id={task_id}, status={status}"
                )
            await asyncio.sleep(self._poll_interval_seconds)

        raise CustomException(msg=f"阿里百炼 ASR 任务超时: task_id={task_id}")

    async def _fetch_transcription_payload(self, transcription_url: str) -> dict[str, Any]:
        """下载百炼转写 JSON。"""
        response = await self._request_json(
            method="GET",
            raw_url=transcription_url,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise CustomException(
                msg=f"阿里百炼转写结果不是 JSON: {response.text[:500]}"
            ) from exc
        if not isinstance(payload, dict):
            raise CustomException(msg="阿里百炼转写结果不是对象")
        return payload

    def _parse_transcription_payload(
        self,
        *,
        payload: dict[str, Any],
        task_id: str,
        request_id: str,
        log_id: str | None,
        transcription_url: str,
    ) -> SpeechRecognitionResult:
        """把百炼转写结果归一化为内部结构。"""
        transcripts_payload = payload.get("transcripts") or []
        if not isinstance(transcripts_payload, list):
            raise CustomException(msg="阿里百炼转写结果缺少 transcripts")

        utterances: list[SpeechUtterance] = []
        text_chunks: list[str] = []
        for transcript_payload in transcripts_payload:
            if not isinstance(transcript_payload, dict):
                continue
            for sentence_payload in transcript_payload.get("sentences") or []:
                if not isinstance(sentence_payload, dict):
                    continue
                words = self._parse_words(sentence_payload.get("words") or [])
                sentence_text = str(sentence_payload.get("text") or "").strip()
                if not sentence_text and words:
                    sentence_text = self._rebuild_text_from_words(words).strip()
                if not sentence_text:
                    continue
                utterance = SpeechUtterance(
                    text=sentence_text,
                    start_time_ms=self._to_int(sentence_payload.get("begin_time")) or 0,
                    end_time_ms=(
                        self._to_int(sentence_payload.get("end_time"))
                        or self._to_int(sentence_payload.get("begin_time"))
                        or 0
                    ),
                    words=words,
                    speaker_id=self._to_int(sentence_payload.get("speaker_id")),
                    language=str(sentence_payload.get("language") or "").strip() or None,
                    emotion=str(sentence_payload.get("emotion") or "").strip() or None,
                )
                utterances.append(utterance)
                text_chunks.append(sentence_text)

        if not utterances:
            raise CustomException(msg="阿里百炼转写完成但未返回句段结果")

        original_duration_ms = self._to_int(
            (payload.get("properties") or {}).get("original_duration_in_milliseconds")
        )
        return SpeechRecognitionResult(
            provider=self.provider_name,
            engine=self._engine_name,
            model=settings.ALIYUN_DASHSCOPE_ASR_MODEL,
            task_id=task_id,
            request_id=request_id,
            log_id=log_id,
            audio_duration_ms=original_duration_ms,
            text="".join(text_chunks).strip(),
            utterances=utterances,
            transcription_url=transcription_url,
        )

    @classmethod
    def _parse_words(cls, words_payload: Any) -> list[SpeechWord]:
        """解析句段内的词级时间戳。"""
        words: list[SpeechWord] = []
        if not isinstance(words_payload, list):
            return words

        for word_payload in words_payload:
            if not isinstance(word_payload, dict):
                continue
            raw_text = str(word_payload.get("text") or "")
            text, text_punctuation = cls._split_word_and_punctuation(raw_text)
            punctuation = (
                str(word_payload.get("punctuation") or "").strip()
                or text_punctuation
                or None
            )
            text = text.strip()
            if not text and not punctuation:
                continue
            words.append(
                SpeechWord(
                    text=text,
                    start_time_ms=cls._to_int(word_payload.get("begin_time")) or 0,
                    end_time_ms=(
                        cls._to_int(word_payload.get("end_time"))
                        or cls._to_int(word_payload.get("begin_time"))
                        or 0
                    ),
                    punctuation=punctuation,
                    confidence=cls._to_float(word_payload.get("confidence")),
                )
            )
        return words

    @staticmethod
    def _split_word_and_punctuation(raw_text: str) -> tuple[str, str | None]:
        """从词文本尾部拆出标点，兼容不同模型的返回格式。"""
        if not raw_text:
            return "", None
        punctuation_chars = "，,。！？!?、；;：:"
        suffix: list[str] = []
        text = raw_text
        while text and text[-1] in punctuation_chars:
            suffix.append(text[-1])
            text = text[:-1]
        if not suffix:
            return raw_text, None
        suffix.reverse()
        return text, "".join(suffix)

    async def _request_json(
        self,
        *,
        method: str,
        path: str | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        raw_url: str | None = None,
    ) -> httpx.Response:
        """发起 JSON HTTP 请求。"""
        timeout = httpx.Timeout(
            connect=30.0,
            read=self._request_timeout_seconds,
            write=30.0,
            pool=30.0,
        )
        url = raw_url or f"{settings.ALIYUN_DASHSCOPE_BASE_URL.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
            )
        if response.status_code >= 400:
            raise CustomException(
                msg=(
                    "阿里百炼 HTTP 请求失败: "
                    f"status={response.status_code}, url={url}, body={response.text[:500]}"
                )
            )
        return response

    @staticmethod
    def _extract_task_id(response: httpx.Response) -> str:
        """提取提交响应里的 task_id。"""
        payload = _response_json(response)
        task_id = str(
            _nested_get(payload, "output", "task_id")
            or _nested_get(payload, "task_id")
            or ""
        ).strip()
        if not task_id:
            raise CustomException(msg=f"阿里百炼提交成功但未返回 task_id: {payload}")
        return task_id

    @staticmethod
    def _extract_task_status(response: httpx.Response) -> str:
        """提取查询响应里的任务状态。"""
        payload = _response_json(response)
        status = str(
            _nested_get(payload, "output", "task_status")
            or _nested_get(payload, "task_status")
            or ""
        ).strip()
        if not status:
            raise CustomException(msg=f"阿里百炼任务查询未返回 task_status: {payload}")
        return status

    @staticmethod
    def _extract_transcription_url(response: httpx.Response) -> str:
        """提取完成任务里的转写结果地址。"""
        payload = _response_json(response)
        transcription_url = str(
            _nested_get(payload, "output", "result", "transcription_url")
            or _nested_get(payload, "output", "results", 0, "transcription_url")
            or ""
        ).strip()
        if not transcription_url:
            raise CustomException(msg=f"阿里百炼任务完成但未返回 transcription_url: {payload}")
        return transcription_url

    @staticmethod
    def _extract_task_error_message(response: httpx.Response) -> str:
        """提取失败任务的错误信息。"""
        payload = _response_json(response)
        return str(
            _nested_get(payload, "output", "message")
            or _nested_get(payload, "message")
            or _nested_get(payload, "output", "code")
            or _nested_get(payload, "code")
            or "unknown"
        )

    @staticmethod
    def _request_id_from_response(response: httpx.Response) -> str | None:
        """读取 DashScope 请求 ID。"""
        return (
            str(response.headers.get("X-DashScope-Request-Id") or "").strip()
            or None
        )

    @staticmethod
    def _build_oss_bucket() -> oss2.Bucket:
        """创建阿里 OSS bucket 客户端。"""
        auth = oss2.Auth(
            settings.ALIYUN_ACCESS_KEY_ID,
            settings.ALIYUN_ACCESS_KEY_SECRET,
        )
        return oss2.Bucket(
            auth,
            settings.ALIYUN_OSS_ENDPOINT,
            settings.ALIYUN_OSS_BUCKET,
        )

    @classmethod
    def _build_object_key(cls, file_name: str) -> str:
        """生成阿里 ASR 临时音频对象键。"""
        safe_name = Path(file_name).name.replace(" ", "-")
        return (
            f"{settings.ALIYUN_OSS_ASR_OBJECT_PREFIX.rstrip('/')}/"
            f"{uuid4().hex}/{safe_name}"
        )

    def _sign_object_url(self, object_key: str) -> str:
        """生成阿里 ASR 临时音频下载地址。"""
        return self._oss_bucket.sign_url(
            "GET",
            object_key,
            settings.ALIYUN_OSS_ASR_PRESIGNED_EXPIRE_SECONDS,
        )

    @staticmethod
    def _rebuild_text_from_words(words: list[SpeechWord]) -> str:
        """按词级结果重建句子文本。"""
        return "".join(word.display_text() for word in words)

    @staticmethod
    def _to_int(value: Any) -> int | None:
        """把阿里返回值安全转成 int。"""
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        """把阿里返回值安全转成 float。"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _validate_settings() -> None:
        """校验阿里 ASR 和 OSS 配置。"""
        missing_names = [
            name
            for name, value in {
                "ALIYUN_DASHSCOPE_API_KEY": settings.ALIYUN_DASHSCOPE_API_KEY,
                "ALIYUN_ACCESS_KEY_ID": settings.ALIYUN_ACCESS_KEY_ID,
                "ALIYUN_ACCESS_KEY_SECRET": settings.ALIYUN_ACCESS_KEY_SECRET,
                "ALIYUN_OSS_ENDPOINT": settings.ALIYUN_OSS_ENDPOINT,
                "ALIYUN_OSS_BUCKET": settings.ALIYUN_OSS_BUCKET,
            }.items()
            if not value
        ]
        if missing_names:
            raise CustomException(msg=f"阿里 ASR/OSS 配置缺失: {', '.join(missing_names)}")


def _response_json(response: httpx.Response) -> dict[str, Any]:
    """把响应安全解析成 JSON 对象。"""
    try:
        payload = response.json()
    except ValueError as exc:
        raise CustomException(
            msg=f"阿里百炼响应不是 JSON: {response.text[:500]}"
        ) from exc
    if not isinstance(payload, dict):
        raise CustomException(msg="阿里百炼响应不是对象")
    return payload


def _nested_get(payload: Any, *keys: Any) -> Any:
    """读取嵌套字段，兼容数组和对象。"""
    current = payload
    for key in keys:
        if isinstance(key, int):
            if not isinstance(current, list) or key >= len(current):
                return None
            current = current[key]
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current

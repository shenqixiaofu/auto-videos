--
-- PostgreSQL database dump
--

\restrict XtHgo6tsQhuEdNKh15hA2RTTBSfxiXqx9DJbJFNHFfxtyyZ8jR5tz7beQUpdNxG

-- Dumped from database version 17.5 (ServBay)
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: ai; Type: SCHEMA; Schema: -; Owner: root
--

CREATE SCHEMA ai;


ALTER SCHEMA ai OWNER TO root;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agno_schema_versions; Type: TABLE; Schema: ai; Owner: root
--

CREATE TABLE ai.agno_schema_versions (
    table_name character varying NOT NULL,
    version character varying NOT NULL,
    created_at character varying NOT NULL,
    updated_at character varying
);


ALTER TABLE ai.agno_schema_versions OWNER TO root;

--
-- Name: agno_sessions; Type: TABLE; Schema: ai; Owner: root
--

CREATE TABLE ai.agno_sessions (
    session_id character varying NOT NULL,
    session_type character varying NOT NULL,
    agent_id character varying,
    team_id character varying,
    workflow_id character varying,
    user_id character varying,
    session_data jsonb,
    agent_data jsonb,
    team_data jsonb,
    workflow_data jsonb,
    metadata jsonb,
    runs jsonb,
    summary jsonb,
    created_at bigint NOT NULL,
    updated_at bigint
);


ALTER TABLE ai.agno_sessions OWNER TO root;

--
-- Name: app_myapp; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.app_myapp (
    name character varying(64) NOT NULL,
    access_url character varying(500) NOT NULL,
    icon_url character varying(300),
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.app_myapp OWNER TO root;

--
-- Name: TABLE app_myapp; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.app_myapp IS '应用系统表';


--
-- Name: COLUMN app_myapp.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.name IS '应用名称';


--
-- Name: COLUMN app_myapp.access_url; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.access_url IS '访问地址';


--
-- Name: COLUMN app_myapp.icon_url; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.icon_url IS '应用图标URL';


--
-- Name: COLUMN app_myapp.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.id IS '主键ID';


--
-- Name: COLUMN app_myapp.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN app_myapp.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN app_myapp.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.description IS '备注/描述';


--
-- Name: COLUMN app_myapp.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.created_time IS '创建时间';


--
-- Name: COLUMN app_myapp.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.updated_time IS '更新时间';


--
-- Name: COLUMN app_myapp.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.created_id IS '创建人ID';


--
-- Name: COLUMN app_myapp.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.app_myapp.updated_id IS '更新人ID';


--
-- Name: app_myapp_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.app_myapp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.app_myapp_id_seq OWNER TO root;

--
-- Name: app_myapp_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.app_myapp_id_seq OWNED BY public.app_myapp.id;


--
-- Name: apscheduler_jobs; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.apscheduler_jobs (
    id character varying(191) NOT NULL,
    next_run_time double precision,
    job_state bytea NOT NULL
);


ALTER TABLE public.apscheduler_jobs OWNER TO root;

--
-- Name: gen_demo; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.gen_demo (
    name character varying(64) NOT NULL,
    a integer,
    b bigint,
    c double precision,
    d boolean NOT NULL,
    e date,
    f time without time zone,
    g timestamp without time zone,
    h text,
    i json,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.gen_demo OWNER TO root;

--
-- Name: TABLE gen_demo; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.gen_demo IS '示例表';


--
-- Name: COLUMN gen_demo.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.name IS '名称';


--
-- Name: COLUMN gen_demo.a; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.a IS '整数';


--
-- Name: COLUMN gen_demo.b; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.b IS '大整数';


--
-- Name: COLUMN gen_demo.c; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.c IS '浮点数';


--
-- Name: COLUMN gen_demo.d; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.d IS '布尔型';


--
-- Name: COLUMN gen_demo.e; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.e IS '日期';


--
-- Name: COLUMN gen_demo.f; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.f IS '时间';


--
-- Name: COLUMN gen_demo.g; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.g IS '日期时间';


--
-- Name: COLUMN gen_demo.h; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.h IS '长文本';


--
-- Name: COLUMN gen_demo.i; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.i IS '元数据(JSON格式)';


--
-- Name: COLUMN gen_demo.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.id IS '主键ID';


--
-- Name: COLUMN gen_demo.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN gen_demo.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN gen_demo.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.description IS '备注/描述';


--
-- Name: COLUMN gen_demo.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.created_time IS '创建时间';


--
-- Name: COLUMN gen_demo.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.updated_time IS '更新时间';


--
-- Name: COLUMN gen_demo.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.created_id IS '创建人ID';


--
-- Name: COLUMN gen_demo.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_demo.updated_id IS '更新人ID';


--
-- Name: gen_demo_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.gen_demo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gen_demo_id_seq OWNER TO root;

--
-- Name: gen_demo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.gen_demo_id_seq OWNED BY public.gen_demo.id;


--
-- Name: gen_table; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.gen_table (
    table_name character varying(200) NOT NULL,
    table_comment character varying(500),
    class_name character varying(100) NOT NULL,
    package_name character varying(100),
    module_name character varying(30),
    business_name character varying(30),
    function_name character varying(100),
    sub_table_name character varying(64) DEFAULT NULL::character varying,
    sub_table_fk_name character varying(64) DEFAULT NULL::character varying,
    parent_menu_id integer,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.gen_table OWNER TO root;

--
-- Name: TABLE gen_table; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.gen_table IS '代码生成表';


--
-- Name: COLUMN gen_table.table_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.table_name IS '表名称';


--
-- Name: COLUMN gen_table.table_comment; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.table_comment IS '表描述';


--
-- Name: COLUMN gen_table.class_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.class_name IS '实体类名称';


--
-- Name: COLUMN gen_table.package_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.package_name IS '生成包路径';


--
-- Name: COLUMN gen_table.module_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.module_name IS '生成模块名';


--
-- Name: COLUMN gen_table.business_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.business_name IS '生成业务名';


--
-- Name: COLUMN gen_table.function_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.function_name IS '生成功能名';


--
-- Name: COLUMN gen_table.sub_table_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.sub_table_name IS '关联子表的表名';


--
-- Name: COLUMN gen_table.sub_table_fk_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.sub_table_fk_name IS '子表关联的外键名';


--
-- Name: COLUMN gen_table.parent_menu_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.parent_menu_id IS '父菜单ID';


--
-- Name: COLUMN gen_table.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.id IS '主键ID';


--
-- Name: COLUMN gen_table.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN gen_table.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN gen_table.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.description IS '备注/描述';


--
-- Name: COLUMN gen_table.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.created_time IS '创建时间';


--
-- Name: COLUMN gen_table.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.updated_time IS '更新时间';


--
-- Name: COLUMN gen_table.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.created_id IS '创建人ID';


--
-- Name: COLUMN gen_table.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table.updated_id IS '更新人ID';


--
-- Name: gen_table_column; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.gen_table_column (
    column_name character varying(200) NOT NULL,
    column_comment character varying(500),
    column_type character varying(100) NOT NULL,
    column_length character varying(50),
    column_default character varying(200),
    is_pk boolean DEFAULT false NOT NULL,
    is_increment boolean DEFAULT false NOT NULL,
    is_nullable boolean DEFAULT true NOT NULL,
    is_unique boolean DEFAULT false NOT NULL,
    python_type character varying(100),
    python_field character varying(200),
    is_insert boolean DEFAULT true NOT NULL,
    is_edit boolean DEFAULT true NOT NULL,
    is_list boolean DEFAULT true NOT NULL,
    is_query boolean DEFAULT false NOT NULL,
    query_type character varying(50),
    html_type character varying(100),
    dict_type character varying(200),
    sort integer NOT NULL,
    table_id integer NOT NULL,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.gen_table_column OWNER TO root;

--
-- Name: TABLE gen_table_column; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.gen_table_column IS '代码生成表字段';


--
-- Name: COLUMN gen_table_column.column_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.column_name IS '列名称';


--
-- Name: COLUMN gen_table_column.column_comment; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.column_comment IS '列描述';


--
-- Name: COLUMN gen_table_column.column_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.column_type IS '列类型';


--
-- Name: COLUMN gen_table_column.column_length; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.column_length IS '列长度';


--
-- Name: COLUMN gen_table_column.column_default; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.column_default IS '列默认值';


--
-- Name: COLUMN gen_table_column.is_pk; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_pk IS '是否主键';


--
-- Name: COLUMN gen_table_column.is_increment; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_increment IS '是否自增';


--
-- Name: COLUMN gen_table_column.is_nullable; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_nullable IS '是否允许为空';


--
-- Name: COLUMN gen_table_column.is_unique; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_unique IS '是否唯一';


--
-- Name: COLUMN gen_table_column.python_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.python_type IS 'Python类型';


--
-- Name: COLUMN gen_table_column.python_field; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.python_field IS 'Python字段名';


--
-- Name: COLUMN gen_table_column.is_insert; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_insert IS '是否为新增字段';


--
-- Name: COLUMN gen_table_column.is_edit; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_edit IS '是否编辑字段';


--
-- Name: COLUMN gen_table_column.is_list; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_list IS '是否列表字段';


--
-- Name: COLUMN gen_table_column.is_query; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.is_query IS '是否查询字段';


--
-- Name: COLUMN gen_table_column.query_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.query_type IS '查询方式';


--
-- Name: COLUMN gen_table_column.html_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.html_type IS '显示类型';


--
-- Name: COLUMN gen_table_column.dict_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.dict_type IS '字典类型';


--
-- Name: COLUMN gen_table_column.sort; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.sort IS '排序';


--
-- Name: COLUMN gen_table_column.table_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.table_id IS '归属表编号';


--
-- Name: COLUMN gen_table_column.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.id IS '主键ID';


--
-- Name: COLUMN gen_table_column.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN gen_table_column.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN gen_table_column.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.description IS '备注/描述';


--
-- Name: COLUMN gen_table_column.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.created_time IS '创建时间';


--
-- Name: COLUMN gen_table_column.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.updated_time IS '更新时间';


--
-- Name: COLUMN gen_table_column.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.created_id IS '创建人ID';


--
-- Name: COLUMN gen_table_column.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.gen_table_column.updated_id IS '更新人ID';


--
-- Name: gen_table_column_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.gen_table_column_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gen_table_column_id_seq OWNER TO root;

--
-- Name: gen_table_column_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.gen_table_column_id_seq OWNED BY public.gen_table_column.id;


--
-- Name: gen_table_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.gen_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gen_table_id_seq OWNER TO root;

--
-- Name: gen_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.gen_table_id_seq OWNED BY public.gen_table.id;


--
-- Name: sys_dept; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_dept (
    name character varying(64) NOT NULL,
    "order" integer NOT NULL,
    code character varying(16),
    leader character varying(32),
    phone character varying(11),
    email character varying(64),
    parent_id integer,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_dept OWNER TO root;

--
-- Name: TABLE sys_dept; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_dept IS '部门表';


--
-- Name: COLUMN sys_dept.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.name IS '部门名称';


--
-- Name: COLUMN sys_dept."order"; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept."order" IS '显示排序';


--
-- Name: COLUMN sys_dept.code; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.code IS '部门编码';


--
-- Name: COLUMN sys_dept.leader; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.leader IS '部门负责人';


--
-- Name: COLUMN sys_dept.phone; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.phone IS '手机';


--
-- Name: COLUMN sys_dept.email; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.email IS '邮箱';


--
-- Name: COLUMN sys_dept.parent_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.parent_id IS '父级部门ID';


--
-- Name: COLUMN sys_dept.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.id IS '主键ID';


--
-- Name: COLUMN sys_dept.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_dept.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_dept.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.description IS '备注/描述';


--
-- Name: COLUMN sys_dept.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.created_time IS '创建时间';


--
-- Name: COLUMN sys_dept.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dept.updated_time IS '更新时间';


--
-- Name: sys_dept_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_dept_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_dept_id_seq OWNER TO root;

--
-- Name: sys_dept_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_dept_id_seq OWNED BY public.sys_dept.id;


--
-- Name: sys_dict_data; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_dict_data (
    dict_sort integer NOT NULL,
    dict_label character varying(255) NOT NULL,
    dict_value character varying(255) NOT NULL,
    css_class character varying(255),
    list_class character varying(255),
    is_default boolean NOT NULL,
    dict_type character varying(255) NOT NULL,
    dict_type_id integer NOT NULL,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_dict_data OWNER TO root;

--
-- Name: TABLE sys_dict_data; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_dict_data IS '字典数据表';


--
-- Name: COLUMN sys_dict_data.dict_sort; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.dict_sort IS '字典排序';


--
-- Name: COLUMN sys_dict_data.dict_label; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.dict_label IS '字典标签';


--
-- Name: COLUMN sys_dict_data.dict_value; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.dict_value IS '字典键值';


--
-- Name: COLUMN sys_dict_data.css_class; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.css_class IS '样式属性（其他样式扩展）';


--
-- Name: COLUMN sys_dict_data.list_class; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.list_class IS '表格回显样式';


--
-- Name: COLUMN sys_dict_data.is_default; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.is_default IS '是否默认（True是 False否）';


--
-- Name: COLUMN sys_dict_data.dict_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.dict_type IS '字典类型';


--
-- Name: COLUMN sys_dict_data.dict_type_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.dict_type_id IS '字典类型ID';


--
-- Name: COLUMN sys_dict_data.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.id IS '主键ID';


--
-- Name: COLUMN sys_dict_data.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_dict_data.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_dict_data.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.description IS '备注/描述';


--
-- Name: COLUMN sys_dict_data.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.created_time IS '创建时间';


--
-- Name: COLUMN sys_dict_data.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_data.updated_time IS '更新时间';


--
-- Name: sys_dict_data_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_dict_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_dict_data_id_seq OWNER TO root;

--
-- Name: sys_dict_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_dict_data_id_seq OWNED BY public.sys_dict_data.id;


--
-- Name: sys_dict_type; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_dict_type (
    dict_name character varying(64) NOT NULL,
    dict_type character varying(255) NOT NULL,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_dict_type OWNER TO root;

--
-- Name: TABLE sys_dict_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_dict_type IS '字典类型表';


--
-- Name: COLUMN sys_dict_type.dict_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.dict_name IS '字典名称';


--
-- Name: COLUMN sys_dict_type.dict_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.dict_type IS '字典类型';


--
-- Name: COLUMN sys_dict_type.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.id IS '主键ID';


--
-- Name: COLUMN sys_dict_type.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_dict_type.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_dict_type.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.description IS '备注/描述';


--
-- Name: COLUMN sys_dict_type.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.created_time IS '创建时间';


--
-- Name: COLUMN sys_dict_type.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_dict_type.updated_time IS '更新时间';


--
-- Name: sys_dict_type_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_dict_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_dict_type_id_seq OWNER TO root;

--
-- Name: sys_dict_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_dict_type_id_seq OWNED BY public.sys_dict_type.id;


--
-- Name: sys_log; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_log (
    type integer NOT NULL,
    request_path character varying(255) NOT NULL,
    request_method character varying(10) NOT NULL,
    request_payload text,
    request_ip character varying(50),
    login_location character varying(255),
    request_os character varying(64),
    request_browser character varying(64),
    response_code integer NOT NULL,
    response_json text,
    process_time character varying(20),
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.sys_log OWNER TO root;

--
-- Name: TABLE sys_log; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_log IS '系统日志表';


--
-- Name: COLUMN sys_log.type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.type IS '日志类型(1登录日志 2操作日志)';


--
-- Name: COLUMN sys_log.request_path; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_path IS '请求路径';


--
-- Name: COLUMN sys_log.request_method; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_method IS '请求方式';


--
-- Name: COLUMN sys_log.request_payload; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_payload IS '请求体';


--
-- Name: COLUMN sys_log.request_ip; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_ip IS '请求IP地址';


--
-- Name: COLUMN sys_log.login_location; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.login_location IS '登录位置';


--
-- Name: COLUMN sys_log.request_os; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_os IS '操作系统';


--
-- Name: COLUMN sys_log.request_browser; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.request_browser IS '浏览器';


--
-- Name: COLUMN sys_log.response_code; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.response_code IS '响应状态码';


--
-- Name: COLUMN sys_log.response_json; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.response_json IS '响应体';


--
-- Name: COLUMN sys_log.process_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.process_time IS '处理时间';


--
-- Name: COLUMN sys_log.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.id IS '主键ID';


--
-- Name: COLUMN sys_log.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_log.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_log.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.description IS '备注/描述';


--
-- Name: COLUMN sys_log.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.created_time IS '创建时间';


--
-- Name: COLUMN sys_log.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.updated_time IS '更新时间';


--
-- Name: COLUMN sys_log.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.created_id IS '创建人ID';


--
-- Name: COLUMN sys_log.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_log.updated_id IS '更新人ID';


--
-- Name: sys_log_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_log_id_seq OWNER TO root;

--
-- Name: sys_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_log_id_seq OWNED BY public.sys_log.id;


--
-- Name: sys_menu; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_menu (
    name character varying(50) NOT NULL,
    type integer NOT NULL,
    "order" integer NOT NULL,
    permission character varying(100),
    icon character varying(50),
    route_name character varying(100),
    route_path character varying(200),
    component_path character varying(200),
    redirect character varying(200),
    hidden boolean NOT NULL,
    keep_alive boolean NOT NULL,
    always_show boolean NOT NULL,
    title character varying(50),
    params json,
    affix boolean NOT NULL,
    parent_id integer,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_menu OWNER TO root;

--
-- Name: TABLE sys_menu; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_menu IS '菜单表';


--
-- Name: COLUMN sys_menu.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.name IS '菜单名称';


--
-- Name: COLUMN sys_menu.type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.type IS '菜单类型(1:目录 2:菜单 3:按钮/权限 4:链接)';


--
-- Name: COLUMN sys_menu."order"; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu."order" IS '显示排序';


--
-- Name: COLUMN sys_menu.permission; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.permission IS '权限标识(如:module_system:user:query)';


--
-- Name: COLUMN sys_menu.icon; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.icon IS '菜单图标';


--
-- Name: COLUMN sys_menu.route_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.route_name IS '路由名称';


--
-- Name: COLUMN sys_menu.route_path; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.route_path IS '路由路径';


--
-- Name: COLUMN sys_menu.component_path; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.component_path IS '组件路径';


--
-- Name: COLUMN sys_menu.redirect; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.redirect IS '重定向地址';


--
-- Name: COLUMN sys_menu.hidden; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.hidden IS '是否隐藏(True:隐藏 False:显示)';


--
-- Name: COLUMN sys_menu.keep_alive; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.keep_alive IS '是否缓存(True:是 False:否)';


--
-- Name: COLUMN sys_menu.always_show; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.always_show IS '是否始终显示(True:是 False:否)';


--
-- Name: COLUMN sys_menu.title; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.title IS '菜单标题';


--
-- Name: COLUMN sys_menu.params; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.params IS '路由参数(JSON对象)';


--
-- Name: COLUMN sys_menu.affix; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.affix IS '是否固定标签页(True:是 False:否)';


--
-- Name: COLUMN sys_menu.parent_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.parent_id IS '父菜单ID';


--
-- Name: COLUMN sys_menu.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.id IS '主键ID';


--
-- Name: COLUMN sys_menu.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_menu.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_menu.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.description IS '备注/描述';


--
-- Name: COLUMN sys_menu.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.created_time IS '创建时间';


--
-- Name: COLUMN sys_menu.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_menu.updated_time IS '更新时间';


--
-- Name: sys_menu_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_menu_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_menu_id_seq OWNER TO root;

--
-- Name: sys_menu_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_menu_id_seq OWNED BY public.sys_menu.id;


--
-- Name: sys_notice; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_notice (
    notice_title character varying(64) NOT NULL,
    notice_type character varying(1) NOT NULL,
    notice_content text,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.sys_notice OWNER TO root;

--
-- Name: TABLE sys_notice; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_notice IS '通知公告表';


--
-- Name: COLUMN sys_notice.notice_title; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.notice_title IS '公告标题';


--
-- Name: COLUMN sys_notice.notice_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.notice_type IS '公告类型(1通知 2公告)';


--
-- Name: COLUMN sys_notice.notice_content; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.notice_content IS '公告内容';


--
-- Name: COLUMN sys_notice.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.id IS '主键ID';


--
-- Name: COLUMN sys_notice.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_notice.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_notice.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.description IS '备注/描述';


--
-- Name: COLUMN sys_notice.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.created_time IS '创建时间';


--
-- Name: COLUMN sys_notice.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.updated_time IS '更新时间';


--
-- Name: COLUMN sys_notice.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.created_id IS '创建人ID';


--
-- Name: COLUMN sys_notice.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_notice.updated_id IS '更新人ID';


--
-- Name: sys_notice_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_notice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_notice_id_seq OWNER TO root;

--
-- Name: sys_notice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_notice_id_seq OWNED BY public.sys_notice.id;


--
-- Name: sys_param; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_param (
    config_name character varying(64) NOT NULL,
    config_key character varying(500) NOT NULL,
    config_value character varying(500),
    config_type boolean,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_param OWNER TO root;

--
-- Name: TABLE sys_param; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_param IS '系统参数表';


--
-- Name: COLUMN sys_param.config_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.config_name IS '参数名称';


--
-- Name: COLUMN sys_param.config_key; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.config_key IS '参数键名';


--
-- Name: COLUMN sys_param.config_value; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.config_value IS '参数键值';


--
-- Name: COLUMN sys_param.config_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.config_type IS '系统内置(True:是 False:否)';


--
-- Name: COLUMN sys_param.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.id IS '主键ID';


--
-- Name: COLUMN sys_param.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_param.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_param.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.description IS '备注/描述';


--
-- Name: COLUMN sys_param.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.created_time IS '创建时间';


--
-- Name: COLUMN sys_param.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_param.updated_time IS '更新时间';


--
-- Name: sys_param_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_param_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_param_id_seq OWNER TO root;

--
-- Name: sys_param_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_param_id_seq OWNED BY public.sys_param.id;


--
-- Name: sys_position; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_position (
    name character varying(64) NOT NULL,
    "order" integer NOT NULL,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.sys_position OWNER TO root;

--
-- Name: TABLE sys_position; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_position IS '岗位表';


--
-- Name: COLUMN sys_position.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.name IS '岗位名称';


--
-- Name: COLUMN sys_position."order"; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position."order" IS '显示排序';


--
-- Name: COLUMN sys_position.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.id IS '主键ID';


--
-- Name: COLUMN sys_position.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_position.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_position.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.description IS '备注/描述';


--
-- Name: COLUMN sys_position.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.created_time IS '创建时间';


--
-- Name: COLUMN sys_position.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.updated_time IS '更新时间';


--
-- Name: COLUMN sys_position.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.created_id IS '创建人ID';


--
-- Name: COLUMN sys_position.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_position.updated_id IS '更新人ID';


--
-- Name: sys_position_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_position_id_seq OWNER TO root;

--
-- Name: sys_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_position_id_seq OWNED BY public.sys_position.id;


--
-- Name: sys_role; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_role (
    name character varying(64) NOT NULL,
    code character varying(16),
    "order" integer NOT NULL,
    data_scope integer NOT NULL,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.sys_role OWNER TO root;

--
-- Name: TABLE sys_role; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_role IS '角色表';


--
-- Name: COLUMN sys_role.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.name IS '角色名称';


--
-- Name: COLUMN sys_role.code; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.code IS '角色编码';


--
-- Name: COLUMN sys_role."order"; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role."order" IS '显示排序';


--
-- Name: COLUMN sys_role.data_scope; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.data_scope IS '数据权限范围(1:仅本人 2:本部门 3:本部门及以下 4:全部 5:自定义)';


--
-- Name: COLUMN sys_role.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.id IS '主键ID';


--
-- Name: COLUMN sys_role.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_role.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_role.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.description IS '备注/描述';


--
-- Name: COLUMN sys_role.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.created_time IS '创建时间';


--
-- Name: COLUMN sys_role.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role.updated_time IS '更新时间';


--
-- Name: sys_role_depts; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_role_depts (
    role_id integer NOT NULL,
    dept_id integer NOT NULL
);


ALTER TABLE public.sys_role_depts OWNER TO root;

--
-- Name: TABLE sys_role_depts; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_role_depts IS '角色部门关联表';


--
-- Name: COLUMN sys_role_depts.role_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role_depts.role_id IS '角色ID';


--
-- Name: COLUMN sys_role_depts.dept_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role_depts.dept_id IS '部门ID';


--
-- Name: sys_role_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_role_id_seq OWNER TO root;

--
-- Name: sys_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_role_id_seq OWNED BY public.sys_role.id;


--
-- Name: sys_role_menus; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_role_menus (
    role_id integer NOT NULL,
    menu_id integer NOT NULL
);


ALTER TABLE public.sys_role_menus OWNER TO root;

--
-- Name: TABLE sys_role_menus; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_role_menus IS '角色菜单关联表';


--
-- Name: COLUMN sys_role_menus.role_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role_menus.role_id IS '角色ID';


--
-- Name: COLUMN sys_role_menus.menu_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_role_menus.menu_id IS '菜单ID';


--
-- Name: sys_user; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_user (
    username character varying(64) NOT NULL,
    password character varying(255) NOT NULL,
    name character varying(32) NOT NULL,
    mobile character varying(11),
    email character varying(64),
    gender character varying(1),
    avatar character varying(255),
    is_superuser boolean NOT NULL,
    last_login timestamp with time zone,
    gitee_login character varying(32),
    github_login character varying(32),
    wx_login character varying(32),
    qq_login character varying(32),
    dept_id integer,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.sys_user OWNER TO root;

--
-- Name: TABLE sys_user; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_user IS '用户表';


--
-- Name: COLUMN sys_user.username; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.username IS '用户名/登录账号';


--
-- Name: COLUMN sys_user.password; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.password IS '密码哈希';


--
-- Name: COLUMN sys_user.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.name IS '昵称';


--
-- Name: COLUMN sys_user.mobile; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.mobile IS '手机号';


--
-- Name: COLUMN sys_user.email; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.email IS '邮箱';


--
-- Name: COLUMN sys_user.gender; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.gender IS '性别(0:男 1:女 2:未知)';


--
-- Name: COLUMN sys_user.avatar; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.avatar IS '头像URL地址';


--
-- Name: COLUMN sys_user.is_superuser; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.is_superuser IS '是否超管';


--
-- Name: COLUMN sys_user.last_login; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.last_login IS '最后登录时间';


--
-- Name: COLUMN sys_user.gitee_login; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.gitee_login IS 'Gitee登录';


--
-- Name: COLUMN sys_user.github_login; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.github_login IS 'Github登录';


--
-- Name: COLUMN sys_user.wx_login; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.wx_login IS '微信登录';


--
-- Name: COLUMN sys_user.qq_login; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.qq_login IS 'QQ登录';


--
-- Name: COLUMN sys_user.dept_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.dept_id IS '部门ID';


--
-- Name: COLUMN sys_user.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.id IS '主键ID';


--
-- Name: COLUMN sys_user.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN sys_user.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN sys_user.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.description IS '备注/描述';


--
-- Name: COLUMN sys_user.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.created_time IS '创建时间';


--
-- Name: COLUMN sys_user.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.updated_time IS '更新时间';


--
-- Name: COLUMN sys_user.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.created_id IS '创建人ID';


--
-- Name: COLUMN sys_user.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user.updated_id IS '更新人ID';


--
-- Name: sys_user_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.sys_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sys_user_id_seq OWNER TO root;

--
-- Name: sys_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.sys_user_id_seq OWNED BY public.sys_user.id;


--
-- Name: sys_user_positions; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_user_positions (
    user_id integer NOT NULL,
    position_id integer NOT NULL
);


ALTER TABLE public.sys_user_positions OWNER TO root;

--
-- Name: TABLE sys_user_positions; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_user_positions IS '用户岗位关联表';


--
-- Name: COLUMN sys_user_positions.user_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user_positions.user_id IS '用户ID';


--
-- Name: COLUMN sys_user_positions.position_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user_positions.position_id IS '岗位ID';


--
-- Name: sys_user_roles; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.sys_user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE public.sys_user_roles OWNER TO root;

--
-- Name: TABLE sys_user_roles; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.sys_user_roles IS '用户角色关联表';


--
-- Name: COLUMN sys_user_roles.user_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user_roles.user_id IS '用户ID';


--
-- Name: COLUMN sys_user_roles.role_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.sys_user_roles.role_id IS '角色ID';


--
-- Name: task_job; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.task_job (
    job_id character varying(64) NOT NULL,
    job_name character varying(128),
    trigger_type character varying(32),
    status character varying(16) NOT NULL,
    next_run_time character varying(64),
    job_state text,
    result text,
    error text,
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL
);


ALTER TABLE public.task_job OWNER TO root;

--
-- Name: TABLE task_job; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.task_job IS '任务执行日志表';


--
-- Name: COLUMN task_job.job_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.job_id IS '任务ID';


--
-- Name: COLUMN task_job.job_name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.job_name IS '任务名称';


--
-- Name: COLUMN task_job.trigger_type; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.trigger_type IS '触发方式: cron/interval/date/manual';


--
-- Name: COLUMN task_job.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.status IS '执行状态';


--
-- Name: COLUMN task_job.next_run_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.next_run_time IS '下次执行时间';


--
-- Name: COLUMN task_job.job_state; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.job_state IS '任务状态信息';


--
-- Name: COLUMN task_job.result; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.result IS '执行结果';


--
-- Name: COLUMN task_job.error; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.error IS '错误信息';


--
-- Name: COLUMN task_job.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.id IS '主键ID';


--
-- Name: COLUMN task_job.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN task_job.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.description IS '备注/描述';


--
-- Name: COLUMN task_job.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.created_time IS '创建时间';


--
-- Name: COLUMN task_job.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_job.updated_time IS '更新时间';


--
-- Name: task_job_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.task_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_job_id_seq OWNER TO root;

--
-- Name: task_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.task_job_id_seq OWNED BY public.task_job.id;


--
-- Name: task_node; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.task_node (
    name character varying(64) NOT NULL,
    code character varying(32) NOT NULL,
    jobstore character varying(64),
    executor character varying(64),
    trigger character varying(64),
    trigger_args text,
    func text,
    args text,
    kwargs text,
    "coalesce" boolean,
    max_instances integer,
    start_date character varying(64),
    end_date character varying(64),
    id integer NOT NULL,
    uuid character varying(64) NOT NULL,
    status character varying(10) NOT NULL,
    description text,
    created_time timestamp without time zone NOT NULL,
    updated_time timestamp without time zone NOT NULL,
    created_id integer,
    updated_id integer
);


ALTER TABLE public.task_node OWNER TO root;

--
-- Name: TABLE task_node; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON TABLE public.task_node IS '节点类型表';


--
-- Name: COLUMN task_node.name; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.name IS '节点名称';


--
-- Name: COLUMN task_node.code; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.code IS '节点编码';


--
-- Name: COLUMN task_node.jobstore; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.jobstore IS '存储器';


--
-- Name: COLUMN task_node.executor; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.executor IS '执行器';


--
-- Name: COLUMN task_node.trigger; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.trigger IS '触发器';


--
-- Name: COLUMN task_node.trigger_args; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.trigger_args IS '触发器参数';


--
-- Name: COLUMN task_node.func; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.func IS '代码块';


--
-- Name: COLUMN task_node.args; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.args IS '位置参数';


--
-- Name: COLUMN task_node.kwargs; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.kwargs IS '关键字参数';


--
-- Name: COLUMN task_node."coalesce"; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node."coalesce" IS '是否合并运行';


--
-- Name: COLUMN task_node.max_instances; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.max_instances IS '最大实例数';


--
-- Name: COLUMN task_node.start_date; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.start_date IS '开始时间';


--
-- Name: COLUMN task_node.end_date; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.end_date IS '结束时间';


--
-- Name: COLUMN task_node.id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.id IS '主键ID';


--
-- Name: COLUMN task_node.uuid; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.uuid IS 'UUID全局唯一标识';


--
-- Name: COLUMN task_node.status; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.status IS '是否启用(0:启用 1:禁用)';


--
-- Name: COLUMN task_node.description; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.description IS '备注/描述';


--
-- Name: COLUMN task_node.created_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.created_time IS '创建时间';


--
-- Name: COLUMN task_node.updated_time; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.updated_time IS '更新时间';


--
-- Name: COLUMN task_node.created_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.created_id IS '创建人ID';


--
-- Name: COLUMN task_node.updated_id; Type: COMMENT; Schema: public; Owner: root
--

COMMENT ON COLUMN public.task_node.updated_id IS '更新人ID';


--
-- Name: task_node_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.task_node_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_node_id_seq OWNER TO root;

--
-- Name: task_node_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.task_node_id_seq OWNED BY public.task_node.id;


--
-- Name: app_myapp id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.app_myapp ALTER COLUMN id SET DEFAULT nextval('public.app_myapp_id_seq'::regclass);


--
-- Name: gen_demo id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_demo ALTER COLUMN id SET DEFAULT nextval('public.gen_demo_id_seq'::regclass);


--
-- Name: gen_table id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table ALTER COLUMN id SET DEFAULT nextval('public.gen_table_id_seq'::regclass);


--
-- Name: gen_table_column id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table_column ALTER COLUMN id SET DEFAULT nextval('public.gen_table_column_id_seq'::regclass);


--
-- Name: sys_dept id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dept ALTER COLUMN id SET DEFAULT nextval('public.sys_dept_id_seq'::regclass);


--
-- Name: sys_dict_data id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_data ALTER COLUMN id SET DEFAULT nextval('public.sys_dict_data_id_seq'::regclass);


--
-- Name: sys_dict_type id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_type ALTER COLUMN id SET DEFAULT nextval('public.sys_dict_type_id_seq'::regclass);


--
-- Name: sys_log id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_log ALTER COLUMN id SET DEFAULT nextval('public.sys_log_id_seq'::regclass);


--
-- Name: sys_menu id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_menu ALTER COLUMN id SET DEFAULT nextval('public.sys_menu_id_seq'::regclass);


--
-- Name: sys_notice id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_notice ALTER COLUMN id SET DEFAULT nextval('public.sys_notice_id_seq'::regclass);


--
-- Name: sys_param id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_param ALTER COLUMN id SET DEFAULT nextval('public.sys_param_id_seq'::regclass);


--
-- Name: sys_position id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_position ALTER COLUMN id SET DEFAULT nextval('public.sys_position_id_seq'::regclass);


--
-- Name: sys_role id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role ALTER COLUMN id SET DEFAULT nextval('public.sys_role_id_seq'::regclass);


--
-- Name: sys_user id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user ALTER COLUMN id SET DEFAULT nextval('public.sys_user_id_seq'::regclass);


--
-- Name: task_job id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_job ALTER COLUMN id SET DEFAULT nextval('public.task_job_id_seq'::regclass);


--
-- Name: task_node id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_node ALTER COLUMN id SET DEFAULT nextval('public.task_node_id_seq'::regclass);


--
-- Data for Name: agno_schema_versions; Type: TABLE DATA; Schema: ai; Owner: root
--

COPY ai.agno_schema_versions (table_name, version, created_at, updated_at) FROM stdin;
agno_sessions	2.5.0	2026-03-10T22:38:46.429268	2026-03-10T22:38:46.429268
\.


--
-- Data for Name: agno_sessions; Type: TABLE DATA; Schema: ai; Owner: root
--

COPY ai.agno_sessions (session_id, session_type, agent_id, team_id, workflow_id, user_id, session_data, agent_data, team_data, workflow_data, metadata, runs, summary, created_at, updated_at) FROM stdin;
d0375348-cc9c-4103-a7ce-18d14560a785	team	\N	1	\N	admin	{"session_name": "新对话", "session_state": {}, "session_metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 898, "total_tokens": 915, "output_tokens": 17, "cache_read_tokens": 320}]}, "input_tokens": 898, "total_tokens": 915, "output_tokens": 17, "cache_read_tokens": 320}}	\N	null	\N	null	[{"input": {"input_content": "你好"}, "model": "deepseek-chat", "tools": [], "run_id": "44f0df2a-aaff-403f-bbb7-de1081d45580", "status": "COMPLETED", "content": "你好！我是你的AI助手，很高兴为你服务。有什么我可以帮助你的吗？", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 898, "total_tokens": 915, "output_tokens": 17, "cache_read_tokens": 320}]}, "duration": 2.4872381659988605, "input_tokens": 898, "total_tokens": 915, "output_tokens": 17, "cache_read_tokens": 320, "time_to_first_token": 2.4092763329990703}, "team_id": "1", "user_id": "admin", "messages": [{"id": "6f9ce5a8-ac26-4ca3-ada9-459641e0225c", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-12 23:50:27.983400.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773330627, "from_history": false, "stop_after_tool_call": false}, {"id": "9ee3931d-2f8f-439a-8495-28c407e1676a", "role": "user", "content": "你好", "created_at": 1773330627, "from_history": false, "stop_after_tool_call": false}, {"id": "900ca747-7b34-44f4-ae74-e6570804fcd0", "role": "assistant", "content": "你好！我是你的AI助手，很高兴为你服务。有什么我可以帮助你的吗？", "metrics": {"duration": 2.3864872499998455, "input_tokens": 898, "total_tokens": 915, "output_tokens": 17, "cache_read_tokens": 320, "time_to_first_token": 2.3864872499998455}, "created_at": 1773330627, "from_history": false, "provider_data": {"id": "ee4835e4-1a1e-4c33-b079-ec99ae7a1b55", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773330627, "session_id": "d0375348-cc9c-4103-a7ce-18d14560a785", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "ee4835e4-1a1e-4c33-b079-ec99ae7a1b55", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}]	null	1773330627	1773330630
0e2076c7-0c72-45c0-a97b-c170413720e9	team	\N	1	\N	admin	{"session_name": "你是男的女的", "session_state": {}, "session_metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 2814, "total_tokens": 2903, "output_tokens": 89, "cache_read_tokens": 960}]}, "input_tokens": 2814, "total_tokens": 2903, "output_tokens": 89, "cache_read_tokens": 960}}	\N	null	\N	null	[{"input": {"input_content": "你是男的女的"}, "model": "deepseek-chat", "events": [], "run_id": "99a1fea8-2950-4f2b-a2f4-63212f52c5fb", "status": "COMPLETED", "content": "我是一个AI助手，没有性别之分。我是由代码和算法构成的数字实体，旨在为您提供帮助和回答问题。\\n\\n如果您有其他问题或需要帮助，请随时告诉我！", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 901, "total_tokens": 936, "output_tokens": 35, "cache_read_tokens": 320}]}, "duration": 3.824642333000156, "input_tokens": 901, "total_tokens": 936, "output_tokens": 35, "cache_read_tokens": 320, "time_to_first_token": 1.7806427080013236}, "team_id": "1", "user_id": "admin", "messages": [{"id": "8539d5ee-a817-4710-822d-99686642c4df", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-13 00:09:08.236156.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773331748, "from_history": false, "stop_after_tool_call": false}, {"id": "18ed9cf5-a2a5-421e-bbb9-946f621d2a2a", "role": "user", "content": "你是男的女的", "created_at": 1773331748, "from_history": false, "stop_after_tool_call": false}, {"id": "7b3a3aa1-1fb8-4f1a-8a2c-298fef38cd7e", "role": "assistant", "content": "我是一个AI助手，没有性别之分。我是由代码和算法构成的数字实体，旨在为您提供帮助和回答问题。\\n\\n如果您有其他问题或需要帮助，请随时告诉我！", "metrics": {"input_tokens": 901, "total_tokens": 936, "output_tokens": 35, "cache_read_tokens": 320, "time_to_first_token": 1.6999175000000832}, "created_at": 1773331748, "from_history": false, "provider_data": {"id": "a1a3e8f4-dad6-45d6-9338-8c33d060f914", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773331748, "session_id": "0e2076c7-0c72-45c0-a97b-c170413720e9", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "a1a3e8f4-dad6-45d6-9338-8c33d060f914", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}, {"input": {"input_content": "好的我知道了"}, "model": "deepseek-chat", "events": [], "run_id": "9bc121c8-78e2-44b9-9ebd-758d33e845f1", "status": "COMPLETED", "content": "好的！如果您有任何其他问题或需要帮助的地方，随时可以告诉我。我很乐意为您提供帮助！", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 942, "total_tokens": 964, "output_tokens": 22, "cache_read_tokens": 320}]}, "duration": 2.982405832999575, "input_tokens": 942, "total_tokens": 964, "output_tokens": 22, "cache_read_tokens": 320, "time_to_first_token": 1.466743332999613}, "team_id": "1", "user_id": "admin", "messages": [{"id": "854713e7-3220-44c8-8c04-97eae9e9eb03", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-13 00:11:22.906936.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773331882, "from_history": false, "stop_after_tool_call": false}, {"id": "7f39e100-a08f-46b9-ba19-3492e7e9e6bd", "role": "user", "content": "好的我知道了", "created_at": 1773331882, "from_history": false, "stop_after_tool_call": false}, {"id": "318823e2-fb6a-48fd-9692-a5dcb407e77f", "role": "assistant", "content": "好的！如果您有任何其他问题或需要帮助的地方，随时可以告诉我。我很乐意为您提供帮助！", "metrics": {"input_tokens": 942, "total_tokens": 964, "output_tokens": 22, "cache_read_tokens": 320, "time_to_first_token": 1.3560426669992012}, "created_at": 1773331882, "from_history": false, "provider_data": {"id": "d918fcc8-da81-4463-9213-72dcf3109dd8", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773331882, "session_id": "0e2076c7-0c72-45c0-a97b-c170413720e9", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "d918fcc8-da81-4463-9213-72dcf3109dd8", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}, {"input": {"input_content": "以后我再找你"}, "model": "deepseek-chat", "run_id": "5395a65a-f7f6-4c82-b9c3-8e4f75f11312", "status": "COMPLETED", "content": "好的，随时欢迎！我会一直在这里，当您需要帮助、有问题或者想聊天的时候，随时可以回来找我。\\n\\n祝您一切顺利！👋", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 971, "total_tokens": 1003, "output_tokens": 32, "cache_read_tokens": 320}]}, "duration": 3.5782694999998057, "input_tokens": 971, "total_tokens": 1003, "output_tokens": 32, "cache_read_tokens": 320, "time_to_first_token": 1.597690667000279}, "team_id": "1", "user_id": "admin", "messages": [{"id": "96f7f716-55d0-450d-946b-2a932e76cbd4", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-13 00:15:15.297981.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773332115, "from_history": false, "stop_after_tool_call": false}, {"id": "a38aa282-1009-41ca-b637-5e035d3df1cd", "role": "user", "content": "以后我再找你", "created_at": 1773332115, "from_history": false, "stop_after_tool_call": false}, {"id": "bbfae894-e2d8-4ba6-bd9e-192e8a8f7dba", "role": "assistant", "content": "好的，随时欢迎！我会一直在这里，当您需要帮助、有问题或者想聊天的时候，随时可以回来找我。\\n\\n祝您一切顺利！👋", "metrics": {"input_tokens": 971, "total_tokens": 1003, "output_tokens": 32, "cache_read_tokens": 320, "time_to_first_token": 1.5115680420003628}, "created_at": 1773332115, "from_history": false, "provider_data": {"id": "bf2c9e44-0665-45e8-847f-f1b3d06bde6c", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773332115, "session_id": "0e2076c7-0c72-45c0-a97b-c170413720e9", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "bf2c9e44-0665-45e8-847f-f1b3d06bde6c", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}]	null	1773331748	1773332118
70f63e6b-f073-4486-8b17-a98cb4a5f4fa	team	\N	1	\N	admin	{"session_name": "在吗", "session_state": {}, "session_metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 1811, "total_tokens": 1842, "output_tokens": 31, "cache_read_tokens": 640}]}, "input_tokens": 1811, "total_tokens": 1842, "output_tokens": 31, "cache_read_tokens": 640}}	\N	null	\N	null	[{"input": {"input_content": "在吗"}, "model": "deepseek-chat", "events": [], "run_id": "bffc5320-8369-471d-814b-ca66a474f358", "status": "COMPLETED", "content": "我在的！有什么可以帮助您的吗？", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 899, "total_tokens": 907, "output_tokens": 8, "cache_read_tokens": 320}]}, "duration": 2.5330075420006324, "input_tokens": 899, "total_tokens": 907, "output_tokens": 8, "cache_read_tokens": 320, "time_to_first_token": 1.714065957999992}, "team_id": "1", "user_id": "admin", "messages": [{"id": "7a9e0dfd-3750-4dac-913f-bb07ad2e7b20", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-12 23:26:49.742737.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773329209, "from_history": false, "stop_after_tool_call": false}, {"id": "04fdabb1-9f2c-4e9b-b133-b834a3d05ab8", "role": "user", "content": "在吗", "created_at": 1773329209, "from_history": false, "stop_after_tool_call": false}, {"id": "711208f2-81e3-4cd6-94a5-042e75f6cf08", "role": "assistant", "content": "我在的！有什么可以帮助您的吗？", "metrics": {"input_tokens": 899, "total_tokens": 907, "output_tokens": 8, "cache_read_tokens": 320, "time_to_first_token": 1.6393582500004413}, "created_at": 1773329209, "from_history": false, "provider_data": {"id": "8f1c6ef1-d4f3-413b-ba35-575a5f02bcde", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773329209, "session_id": "70f63e6b-f073-4486-8b17-a98cb4a5f4fa", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "8f1c6ef1-d4f3-413b-ba35-575a5f02bcde", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}, {"input": {"input_content": "你是谁"}, "model": "deepseek-chat", "run_id": "2636867a-f6e4-4eca-b201-68f5d0a12ffa", "status": "COMPLETED", "content": "我是您的AI助手，可以帮助您回答问题、提供信息或协助处理各种任务。有什么需要我帮忙的吗？", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 912, "total_tokens": 935, "output_tokens": 23, "cache_read_tokens": 320}]}, "duration": 3.5702720829995087, "input_tokens": 912, "total_tokens": 935, "output_tokens": 23, "cache_read_tokens": 320, "time_to_first_token": 1.6412430000000313}, "team_id": "1", "user_id": "admin", "messages": [{"id": "0c9fc707-6fec-4487-8475-838a7ee9e31b", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-13 00:19:14.591494.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773332354, "from_history": false, "stop_after_tool_call": false}, {"id": "f6c48ec9-213b-4e73-a056-c241b5b9a88e", "role": "user", "content": "你是谁", "created_at": 1773332354, "from_history": false, "stop_after_tool_call": false}, {"id": "c4b61a03-4789-4227-81a6-0ce10c32251b", "role": "assistant", "content": "我是您的AI助手，可以帮助您回答问题、提供信息或协助处理各种任务。有什么需要我帮忙的吗？", "metrics": {"input_tokens": 912, "total_tokens": 935, "output_tokens": 23, "cache_read_tokens": 320, "time_to_first_token": 1.5480335829997784}, "created_at": 1773332354, "from_history": false, "provider_data": {"id": "988b5a84-e099-44a0-99c8-9f5eff841b7a", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773332354, "session_id": "70f63e6b-f073-4486-8b17-a98cb4a5f4fa", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "988b5a84-e099-44a0-99c8-9f5eff841b7a", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}]	null	1773329209	1773332358
8e21f309-8b73-45b9-966a-37220a628620	team	\N	1	\N	admin	{"session_name": "你是谁", "session_state": {}, "session_metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 898, "total_tokens": 931, "output_tokens": 33, "cache_read_tokens": 320}]}, "input_tokens": 898, "total_tokens": 931, "output_tokens": 33, "cache_read_tokens": 320}}	\N	null	\N	null	[{"input": {"input_content": "你是谁"}, "model": "deepseek-chat", "run_id": "973da0dc-6842-4030-bf31-dba0bf305fb8", "status": "COMPLETED", "content": "我是您的AI助手，可以帮助您回答问题和提供帮助。我可以协调一个专门团队来处理各种任务，也可以直接回答简单的问题。\\n\\n有什么我可以为您做的吗？", "metrics": {"details": {"model": [{"id": "deepseek-chat", "provider": "OpenAI", "input_tokens": 898, "total_tokens": 931, "output_tokens": 33, "cache_read_tokens": 320}]}, "duration": 3.7604397920003976, "input_tokens": 898, "total_tokens": 931, "output_tokens": 33, "cache_read_tokens": 320, "time_to_first_token": 1.9425657499996305}, "team_id": "1", "user_id": "admin", "messages": [{"id": "380b9750-36aa-4af2-a44a-457f9c0ed717", "role": "system", "content": "You coordinate a team of specialized AI agents to fulfill the user's request. Delegate to members when their expertise or tools are needed. For straightforward requests you can handle directly — including using your own tools — respond without delegating.\\n\\n<team_members>\\n<member id=\\"admin\\" name=\\"fastapiadmin_agent\\">\\n  Role: You are a helpful AI assistant\\n  Description: 你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。\\n</member>\\n</team_members>\\n\\n<how_to_respond>\\nYou operate in coordinate mode. For requests that need member expertise, select the best member(s), delegate with clear task descriptions, and synthesize their outputs into a unified response. For requests you can handle directly — simple questions, using your own tools, or general conversation — respond without delegating.\\n\\nDelegation:\\n- Match each sub-task to the member whose role and tools are the best fit. Delegate to multiple members when the request spans different areas of expertise.\\n- Write task descriptions that are self-contained: state the goal, provide relevant context from the conversation, and describe what a good result looks like.\\n- Use only the member's ID when delegating — do not prefix it with the team ID.\\n\\nAfter receiving member responses:\\n- If a response is incomplete or off-target, re-delegate with clearer instructions or try a different member.\\n- Synthesize all results into a single coherent response. Resolve contradictions, fill gaps with your own reasoning, and add structure — do not simply concatenate member outputs.\\n</how_to_respond>\\n\\n- 保持回答简洁明了\\n- 如果不确定，请说明\\n<additional_information>\\n- Use markdown to format your answers.\\n- The current time is 2026-03-12 23:42:23.352241.\\n</additional_information>\\n\\n<expected_output>\\n中文回答\\n</expected_output>", "created_at": 1773330143, "from_history": false, "stop_after_tool_call": false}, {"id": "b159f3aa-a036-44c2-b1d6-e6bfe44acbef", "role": "user", "content": "你是谁", "created_at": 1773330143, "from_history": false, "stop_after_tool_call": false}, {"id": "692d4bf2-aaae-4fa1-85cd-8a87fae2e7ac", "role": "assistant", "content": "我是您的AI助手，可以帮助您回答问题和提供帮助。我可以协调一个专门团队来处理各种任务，也可以直接回答简单的问题。\\n\\n有什么我可以为您做的吗？", "metrics": {"input_tokens": 898, "total_tokens": 931, "output_tokens": 33, "cache_read_tokens": 320, "time_to_first_token": 1.8599242089985637}, "created_at": 1773330143, "from_history": false, "provider_data": {"id": "f0a17d67-7f1e-48de-b34b-96a3dec94f4c", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}, "stop_after_tool_call": false}], "created_at": 1773330143, "session_id": "8e21f309-8b73-45b9-966a-37220a628620", "content_type": "str", "model_provider": "OpenAI", "member_responses": [], "model_provider_data": {"id": "f0a17d67-7f1e-48de-b34b-96a3dec94f4c", "system_fingerprint": "fp_eaab8d114b_prod0820_fp8_kvcache"}}]	null	1773330143	1773330147
\.


--
-- Data for Name: app_myapp; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.app_myapp (name, access_url, icon_url, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: apscheduler_jobs; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.apscheduler_jobs (id, next_run_time, job_state) FROM stdin;
\.


--
-- Data for Name: gen_demo; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.gen_demo (name, a, b, c, d, e, f, g, h, i, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: gen_table; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.gen_table (table_name, table_comment, class_name, package_name, module_name, business_name, function_name, sub_table_name, sub_table_fk_name, parent_menu_id, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: gen_table_column; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.gen_table_column (column_name, column_comment, column_type, column_length, column_default, is_pk, is_increment, is_nullable, is_unique, python_type, python_field, is_insert, is_edit, is_list, is_query, query_type, html_type, dict_type, sort, table_id, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: sys_dept; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_dept (name, "order", code, leader, phone, email, parent_id, id, uuid, status, description, created_time, updated_time) FROM stdin;
集团总公司	1	GROUP	部门负责人	1582112620	deptadmin@example.com	\N	1	fca0ba49-0407-4077-bb7a-fef2149b4770	0	集团总公司	2026-03-22 21:43:05.988003	2026-03-22 21:43:05.988004
\.


--
-- Data for Name: sys_dict_data; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_dict_data (dict_sort, dict_label, dict_value, css_class, list_class, is_default, dict_type, dict_type_id, id, uuid, status, description, created_time, updated_time) FROM stdin;
1	男	0	blue	\N	t	sys_user_sex	1	1	5f3455e5-b216-44a3-9b26-a838dfcb536f	0	性别男	2026-03-22 21:43:05.996723	2026-03-22 21:43:05.996725
2	女	1	pink	\N	f	sys_user_sex	1	2	533a5b46-6833-4df3-a0b4-91253a35dc92	0	性别女	2026-03-22 21:43:05.996728	2026-03-22 21:43:05.996729
3	未知	2	red	\N	f	sys_user_sex	1	3	c3438d12-0e66-4a40-925b-ded41de26b9a	0	性别未知	2026-03-22 21:43:05.996732	2026-03-22 21:43:05.996732
1	是	1		primary	t	sys_yes_no	2	4	8b3f19de-819e-495c-a60f-74bc63cb8aad	0	是	2026-03-22 21:43:05.996735	2026-03-22 21:43:05.996735
2	否	0		danger	f	sys_yes_no	2	5	2efc60ed-3d7a-49ce-9f9a-c1befdb58669	0	否	2026-03-22 21:43:05.996738	2026-03-22 21:43:05.996738
1	启用	1		primary	f	sys_common_status	3	6	6bde0c27-1ad9-4ee0-b7b4-ac8c5ed182fe	0	启用状态	2026-03-22 21:43:05.996741	2026-03-22 21:43:05.996741
2	停用	0		danger	f	sys_common_status	3	7	a3001879-db74-4e93-baa3-eb4f815b104c	0	停用状态	2026-03-22 21:43:05.996743	2026-03-22 21:43:05.996744
1	通知	1	blue	warning	t	sys_notice_type	4	8	98c4e4ce-aaec-44ba-9660-b7810c331c96	0	通知	2026-03-22 21:43:05.996746	2026-03-22 21:43:05.996747
2	公告	2	orange	success	f	sys_notice_type	4	9	6d82ff6e-b3b0-4ca8-afc4-5ce68ea550d5	0	公告	2026-03-22 21:43:05.996749	2026-03-22 21:43:05.99675
99	其他	0		info	f	sys_oper_type	5	10	bade7359-9ec9-4fff-ac77-40fa0fe5ca86	0	其他操作	2026-03-22 21:43:05.996752	2026-03-22 21:43:05.996752
1	新增	1		info	f	sys_oper_type	5	11	8d97a4a6-0fc3-4964-b566-0eb4714db566	0	新增操作	2026-03-22 21:43:05.996755	2026-03-22 21:43:05.996755
2	修改	2		info	f	sys_oper_type	5	12	ff1c1c36-d447-4e6d-8d5e-65e0a45d79fd	0	修改操作	2026-03-22 21:43:05.996758	2026-03-22 21:43:05.996758
3	删除	3		danger	f	sys_oper_type	5	13	b3aed89f-33e0-42f9-9371-27cdc62136e3	0	删除操作	2026-03-22 21:43:05.996761	2026-03-22 21:43:05.996761
4	分配权限	4		primary	f	sys_oper_type	5	14	d8d59718-3390-4b5f-b573-c9a2ed923990	0	授权操作	2026-03-22 21:43:05.996763	2026-03-22 21:43:05.996764
5	导出	5		warning	f	sys_oper_type	5	15	8d6c98f7-4c39-49ae-91c1-55ae4ce5f66b	0	导出操作	2026-03-22 21:43:05.996766	2026-03-22 21:43:05.996766
6	导入	6		warning	f	sys_oper_type	5	16	bfab2650-9985-4ac2-a58a-366a04d77550	0	导入操作	2026-03-22 21:43:05.996769	2026-03-22 21:43:05.996769
7	强退	7		danger	f	sys_oper_type	5	17	aab7e128-f889-45da-ae71-1216e98822fc	0	强退操作	2026-03-22 21:43:05.996772	2026-03-22 21:43:05.996772
8	生成代码	8		warning	f	sys_oper_type	5	18	4b68bd5a-97f5-4b74-aa3c-c38102e975e4	0	生成操作	2026-03-22 21:43:05.996774	2026-03-22 21:43:05.996775
9	清空数据	9		danger	f	sys_oper_type	5	19	d56f9b46-b500-44e8-8373-f07f58f9659d	0	清空操作	2026-03-22 21:43:05.996777	2026-03-22 21:43:05.996778
1	默认(Memory)	default		\N	t	sys_job_store	6	20	8d6200ab-4794-4b42-8995-806f8f42e340	0	默认分组	2026-03-22 21:43:05.99678	2026-03-22 21:43:05.99678
2	数据库(Sqlalchemy)	sqlalchemy		\N	f	sys_job_store	6	21	0e6fb93b-fabd-4b06-aed9-d5151ae8606a	0	数据库分组	2026-03-22 21:43:05.996783	2026-03-22 21:43:05.996783
3	数据库(Redis)	redis		\N	f	sys_job_store	6	22	e9f5bfd2-3b04-4d8e-a473-92dc00d257db	0	reids分组	2026-03-22 21:43:05.996786	2026-03-22 21:43:05.996786
1	线程池	default		\N	f	sys_job_executor	7	23	b684ef00-caa3-42c8-a934-874ad8ba81fd	0	线程池	2026-03-22 21:43:05.996789	2026-03-22 21:43:05.996789
2	进程池	processpool		\N	f	sys_job_executor	7	24	eb8125cc-0600-4258-b5b0-cf16e5776842	0	进程池	2026-03-22 21:43:05.996791	2026-03-22 21:43:05.996792
1	演示函数	scheduler_test.job		\N	t	sys_job_function	8	25	c1de5c74-81b8-49c9-9106-9df26d210dcb	0	演示函数	2026-03-22 21:43:05.996794	2026-03-22 21:43:05.996794
1	指定日期(date)	date		\N	t	sys_job_trigger	9	26	ea2e017c-cdd4-4899-9b3a-18a69b5fb6f7	0	指定日期任务触发器	2026-03-22 21:43:05.996797	2026-03-22 21:43:05.996797
2	间隔触发器(interval)	interval		\N	f	sys_job_trigger	9	27	2829bc17-5f31-4bf5-bc66-1ee1d6c05ebb	0	间隔触发器任务触发器	2026-03-22 21:43:05.9968	2026-03-22 21:43:05.9968
3	cron表达式	cron		\N	f	sys_job_trigger	9	28	b135e3c7-6e3a-4a9a-be6f-5881e627fd9e	0	间隔触发器任务触发器	2026-03-22 21:43:05.996803	2026-03-22 21:43:05.996803
1	默认(default)	default		\N	t	sys_list_class	10	29	c7b8a194-b8b6-410d-b2fc-599bd05187e0	0	默认表格回显样式	2026-03-22 21:43:05.996805	2026-03-22 21:43:05.996806
2	主要(primary)	primary		\N	f	sys_list_class	10	30	10ffae69-4fef-4d7b-b617-091496667c74	0	主要表格回显样式	2026-03-22 21:43:05.996808	2026-03-22 21:43:05.996808
3	成功(success)	success		\N	f	sys_list_class	10	31	c9235e14-5c78-4e59-a7f4-87b21f5ae681	0	成功表格回显样式	2026-03-22 21:43:05.996811	2026-03-22 21:43:05.996811
4	信息(info)	info		\N	f	sys_list_class	10	32	3e7616d5-8b42-41ad-bf21-6c92a000d1a5	0	信息表格回显样式	2026-03-22 21:43:05.996814	2026-03-22 21:43:05.996814
5	警告(warning)	warning		\N	f	sys_list_class	10	33	a2a6ac17-9683-47cb-8167-3f2088d1eb75	0	警告表格回显样式	2026-03-22 21:43:05.996816	2026-03-22 21:43:05.996817
6	危险(danger)	danger		\N	f	sys_list_class	10	34	7b187b9f-0404-4c59-a4fd-de6ff32322a6	0	危险表格回显样式	2026-03-22 21:43:05.996819	2026-03-22 21:43:05.99682
\.


--
-- Data for Name: sys_dict_type; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_dict_type (dict_name, dict_type, id, uuid, status, description, created_time, updated_time) FROM stdin;
用户性别	sys_user_sex	1	4ec3f98f-2f0f-437c-a20e-a409ca77bd1d	0	用户性别列表	2026-03-22 21:43:05.992952	2026-03-22 21:43:05.992953
系统是否	sys_yes_no	2	1ce66413-f99f-42fe-963c-320de039ab38	0	系统是否列表	2026-03-22 21:43:05.992957	2026-03-22 21:43:05.992957
系统状态	sys_common_status	3	e313cf3d-a701-403e-9ada-f955d03b0c8f	0	系统状态	2026-03-22 21:43:05.99296	2026-03-22 21:43:05.992961
通知类型	sys_notice_type	4	cf6b0619-d2ef-43bb-8273-cd1acea01cd7	0	通知类型列表	2026-03-22 21:43:05.992963	2026-03-22 21:43:05.992964
操作类型	sys_oper_type	5	a50ddb54-b4fb-4764-888b-0420db7b6612	0	操作类型列表	2026-03-22 21:43:05.992966	2026-03-22 21:43:05.992967
任务存储器	sys_job_store	6	45f96388-b8f1-44d8-be8c-2cad8e5da33c	0	任务分组列表	2026-03-22 21:43:05.992969	2026-03-22 21:43:05.992969
任务执行器	sys_job_executor	7	99bb30ed-9576-4bc7-8f37-aa404bd334d4	0	任务执行器列表	2026-03-22 21:43:05.992972	2026-03-22 21:43:05.992972
任务函数	sys_job_function	8	3077c58f-20f0-4c40-b272-7f465f20bb27	0	任务函数列表	2026-03-22 21:43:05.992975	2026-03-22 21:43:05.992975
任务触发器	sys_job_trigger	9	bb41e39d-0aca-4209-8d3b-f5463a2c80de	0	任务触发器列表	2026-03-22 21:43:05.992978	2026-03-22 21:43:05.992978
表格回显样式	sys_list_class	10	c9dfde76-2843-4cfd-ac53-c49dab01f8e3	0	表格回显样式列表	2026-03-22 21:43:05.992981	2026-03-22 21:43:05.992981
\.


--
-- Data for Name: sys_log; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_log (type, request_path, request_method, request_payload, request_ip, login_location, request_os, request_browser, response_code, response_json, process_time, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: sys_menu; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_menu (name, type, "order", permission, icon, route_name, route_path, component_path, redirect, hidden, keep_alive, always_show, title, params, affix, parent_id, id, uuid, status, description, created_time, updated_time) FROM stdin;
仪表盘	1	1		client	Dashboard	/dashboard	\N	/dashboard/workplace	f	t	t	仪表盘	null	f	\N	1	77723425-e6bb-4118-a50d-ef8a9293a13e	0	初始化数据	2026-03-22 21:43:05.965721	2026-03-22 21:43:05.965725
系统管理	1	2	\N	system	System	/system	\N	/system/menu	f	t	f	系统管理	null	f	\N	2	f75cff57-378a-48d0-8ac2-5710a62b97f4	0	初始化数据	2026-03-22 21:43:05.965729	2026-03-22 21:43:05.96573
监控管理	1	3	\N	monitor	Monitor	/monitor	\N	/monitor/online	f	t	f	监控管理	null	f	\N	3	388d3140-64f3-49eb-b5c0-74b82d0d01f1	0	初始化数据	2026-03-22 21:43:05.965733	2026-03-22 21:43:05.965733
接口管理	1	4	\N	document	Common	/common	\N	/common/docs	f	t	f	接口管理	null	f	\N	4	0813310b-7718-48f3-89e0-a8171a3623ec	0	初始化数据	2026-03-22 21:43:05.965736	2026-03-22 21:43:05.965737
代码管理	1	5	\N	code	Generator	/generator	\N	/generator/gencode	f	t	f	代码管理	null	f	\N	5	6d824a7d-974f-49c3-a709-37a0794ce029	0	代码管理	2026-03-22 21:43:05.965739	2026-03-22 21:43:05.96574
应用管理	1	6	\N	el-icon-ShoppingBag	Application	/application	\N	/application/myapp	f	t	f	应用管理	null	f	\N	6	9555cc91-c8c9-4cec-853d-096af37c3b18	0	初始化数据	2026-03-22 21:43:05.965742	2026-03-22 21:43:05.965743
AI管理	1	7	\N	el-icon-ChatLineSquare	AI	/ai	\N	/ai/chat	f	t	f	AI管理	null	f	\N	7	b69d17ec-8a82-4484-a5d1-3ebd78541eff	0	AI管理	2026-03-22 21:43:05.965745	2026-03-22 21:43:05.965746
任务管理	1	8	\N	el-icon-SetUp	Task	/task	\N	/task/job	f	t	f	任务管理	null	f	\N	8	d721c68d-c0fd-4dba-93cd-5e8b2d7c9032	0	任务管理	2026-03-22 21:43:05.965748	2026-03-22 21:43:05.965749
案例管理	1	9	\N	menu	Example	/example	\N	/example/demo	f	t	f	案例管理	null	f	\N	9	8fcfaf12-40b4-4915-a989-1aeb1d86b134	0	案例管理	2026-03-22 21:43:05.965751	2026-03-22 21:43:05.965751
工作台	2	1	dashboard:workplace:query	el-icon-PieChart	Workplace	/dashboard/workplace	dashboard/workplace	\N	f	t	f	工作台	null	f	1	10	3d081637-bf84-4425-9fdc-134b33b9750c	0	初始化数据	2026-03-22 21:43:05.972053	2026-03-22 21:43:05.972055
菜单管理	2	1	module_system:menu:query	menu	Menu	/system/menu	module_system/menu/index	\N	f	t	f	菜单管理	null	f	2	11	9ddbc906-97fd-484d-8782-9f41fdf674c2	0	初始化数据	2026-03-22 21:43:05.972059	2026-03-22 21:43:05.972059
部门管理	2	2	module_system:dept:query	tree	Dept	/system/dept	module_system/dept/index	\N	f	t	f	部门管理	null	f	2	12	3b17db1a-b573-488d-b9cf-4e454930e513	0	初始化数据	2026-03-22 21:43:05.972063	2026-03-22 21:43:05.972063
岗位管理	2	3	module_system:position:query	el-icon-Coordinate	Position	/system/position	module_system/position/index	\N	f	t	f	岗位管理	null	f	2	13	4c2cd467-67ef-41ca-b553-9ac5e1d348c6	0	初始化数据	2026-03-22 21:43:05.972066	2026-03-22 21:43:05.972066
角色管理	2	4	module_system:role:query	role	Role	/system/role	module_system/role/index	\N	f	t	f	角色管理	null	f	2	14	b0c423bc-035c-4fce-ba39-efb128060003	0	初始化数据	2026-03-22 21:43:05.972069	2026-03-22 21:43:05.97207
用户管理	2	5	module_system:user:query	el-icon-User	User	/system/user	module_system/user/index	\N	f	t	f	用户管理	null	f	2	15	50ec2857-1aee-4c46-acd4-d4ca0a19a30b	0	初始化数据	2026-03-22 21:43:05.972073	2026-03-22 21:43:05.972073
日志管理	2	6	module_system:log:query	el-icon-Aim	Log	/system/log	module_system/log/index	\N	f	t	f	日志管理	null	f	2	16	fe19b3c4-0eef-4500-8f2d-f9e706fb45b7	0	初始化数据	2026-03-22 21:43:05.972077	2026-03-22 21:43:05.972078
公告管理	2	7	module_system:notice:query	bell	Notice	/system/notice	module_system/notice/index	\N	f	t	f	公告管理	null	f	2	17	b34813fa-e2db-4d2a-8402-547ea9028250	0	初始化数据	2026-03-22 21:43:05.972082	2026-03-22 21:43:05.972082
参数管理	2	8	module_system:param:query	setting	Params	/system/param	module_system/param/index	\N	f	t	f	参数管理	null	f	2	18	8fba626f-6ea3-4381-947c-d1bab1e55234	0	初始化数据	2026-03-22 21:43:05.972086	2026-03-22 21:43:05.972086
字典管理	2	9	module_system:dict_type:query	dict	Dict	/system/dict	module_system/dict/index	\N	f	t	f	字典管理	null	f	2	19	a170500c-9463-47d3-8673-062da44499fd	0	初始化数据	2026-03-22 21:43:05.97209	2026-03-22 21:43:05.972091
在线用户	2	1	module_monitor:online:query	el-icon-Headset	MonitorOnline	/monitor/online	module_monitor/online/index	\N	f	t	f	在线用户	null	f	3	20	e2972f11-447f-43f2-9652-718dd64379eb	0	初始化数据	2026-03-22 21:43:05.972094	2026-03-22 21:43:05.972095
服务器监控	2	2	module_monitor:server:query	el-icon-Odometer	MonitorServer	/monitor/server	module_monitor/server/index	\N	f	t	f	服务器监控	null	f	3	21	7f2af927-9713-4da4-b785-e762c24003fb	0	初始化数据	2026-03-22 21:43:05.972098	2026-03-22 21:43:05.972098
缓存监控	2	3	module_monitor:cache:query	el-icon-Stopwatch	MonitorCache	/monitor/cache	module_monitor/cache/index	\N	f	t	f	缓存监控	null	f	3	22	a1a98702-ffef-4d8b-b09e-b93cba357f07	0	初始化数据	2026-03-22 21:43:05.972101	2026-03-22 21:43:05.972102
文件管理	2	4	module_monitor:resource:query	el-icon-Files	Resource	/monitor/resource	module_monitor/resource/index	\N	f	t	f	文件管理	null	f	3	23	eac4916d-5789-4527-bfc9-5483e9eb05ea	0	初始化数据	2026-03-22 21:43:05.972105	2026-03-22 21:43:05.972105
Swagger文档	4	1	module_common:docs:query	api	Docs	/common/docs	module_common/docs/index	\N	f	t	f	Swagger文档	null	f	4	24	71d2e1f4-6284-40b4-b261-67f36ab5449c	0	初始化数据	2026-03-22 21:43:05.972108	2026-03-22 21:43:05.972108
Redoc文档	4	2	module_common:redoc:query	el-icon-Document	Redoc	/common/redoc	module_common/redoc/index	\N	f	t	f	Redoc文档	null	f	4	25	bab8e1ec-00ab-4c1d-afc1-feea1ea82b27	0	初始化数据	2026-03-22 21:43:05.972111	2026-03-22 21:43:05.972112
LangJin文档	4	3	module_common:ljdoc:query	el-icon-Document	Ljdoc	/common/ljdoc	module_common/ljdoc/index	\N	f	t	f	LangJin文档	null	f	4	26	490caaf1-87d5-4767-950e-a2cadafb66fa	0	初始化数据	2026-03-22 21:43:05.972114	2026-03-22 21:43:05.972115
代码生成	2	1	module_generator:gencode:query	code	GenCode	/generator/gencode	module_generator/gencode/index	\N	f	t	f	代码生成	null	f	5	27	432c00b5-1be3-4f67-b25f-ee455b39db70	0	代码生成	2026-03-22 21:43:05.972118	2026-03-22 21:43:05.972118
我的应用	2	1	module_application:myapp:query	el-icon-ShoppingCartFull	MYAPP	/application/myapp	module_application/myapp/index	\N	f	t	f	我的应用	null	f	6	28	bc73934c-d8cc-48a1-99e1-1391f3c8b6b5	0	初始化数据	2026-03-22 21:43:05.972121	2026-03-22 21:43:05.972121
AI智能助手	2	1	module_ai:chat:query	el-icon-ChatDotRound	Chat	/ai/chat	module_ai/chat/index	\N	f	t	f	AI智能助手	null	f	7	29	7cc17587-77a5-4579-b5c1-dd437be68bff	0	AI智能助手	2026-03-22 21:43:05.972124	2026-03-22 21:43:05.972124
会话记忆	2	2	module_ai:chat:query	el-icon-ChatLineSquare	Memory	/ai/memory	module_ai/memory/index	\N	f	t	f	会话记忆	null	f	7	30	53c4f9f9-67ec-41b6-8d3b-55f033951c6d	0	会话记忆管理	2026-03-22 21:43:05.972127	2026-03-22 21:43:05.972127
调度器监控	2	1	module_task:job:query	el-icon-DataLine	Job	/task/job	module_task/job/index	\N	f	t	f	调度器监控	null	f	8	31	e6c7b026-c097-4743-a39d-57638dbaeb8e	0	调度器监控	2026-03-22 21:43:05.97213	2026-03-22 21:43:05.972131
节点管理	2	2	module_task:node:query	el-icon-Postcard	Node	/task/node	module_task/node/index	\N	f	t	f	节点管理	null	f	8	32	7eb72189-1bca-4165-9063-23b79f990b4f	0	节点管理	2026-03-22 21:43:05.972133	2026-03-22 21:43:05.972134
示例管理	2	1	module_example:demo:query	menu	Demo	/example/demo	module_example/demo/index	\N	f	t	f	示例管理	null	f	9	33	944e0375-5c7a-48f9-a776-aa3d5cbd6d62	0	示例管理	2026-03-22 21:43:05.972137	2026-03-22 21:43:05.972137
创建菜单	3	1	module_system:menu:create	\N	\N	\N	\N	\N	f	t	f	创建菜单	null	f	11	34	092c4360-94be-4b10-97f6-57afbe72101b	0	初始化数据	2026-03-22 21:43:05.976755	2026-03-22 21:43:05.976756
修改菜单	3	2	module_system:menu:update	\N	\N	\N	\N	\N	f	t	f	修改菜单	null	f	11	35	32a7208c-73ba-4bc4-90fd-0dde46285ac6	0	初始化数据	2026-03-22 21:43:05.97676	2026-03-22 21:43:05.976761
删除菜单	3	3	module_system:menu:delete	\N	\N	\N	\N	\N	f	t	f	删除菜单	null	f	11	36	acc2578e-4595-4c19-9bfc-315e616cc83b	0	初始化数据	2026-03-22 21:43:05.976764	2026-03-22 21:43:05.976764
批量修改菜单状态	3	4	module_system:menu:patch	\N	\N	\N	\N	\N	f	t	f	批量修改菜单状态	null	f	11	37	ea0e3e7f-f7b9-4380-8bdc-caceafea4887	0	初始化数据	2026-03-22 21:43:05.976767	2026-03-22 21:43:05.976767
详情菜单	3	5	module_system:menu:detail	\N	\N	\N	\N	\N	f	t	f	详情菜单	null	f	11	38	bec696d9-c9f7-4f2a-b18f-2c7dddb5d031	0	初始化数据	2026-03-22 21:43:05.97677	2026-03-22 21:43:05.97677
查询菜单	3	6	module_system:menu:query	\N	\N	\N	\N	\N	f	t	f	查询菜单	null	f	11	39	9ff85b96-2dab-490b-9a93-e6158badd17b	0	初始化数据	2026-03-22 21:43:05.976772	2026-03-22 21:43:05.976773
创建部门	3	1	module_system:dept:create	\N	\N	\N	\N	\N	f	t	f	创建部门	null	f	12	40	714758bc-5323-4dc4-b8c4-2b5502d54501	0	初始化数据	2026-03-22 21:43:05.976775	2026-03-22 21:43:05.976776
修改部门	3	2	module_system:dept:update	\N	\N	\N	\N	\N	f	t	f	修改部门	null	f	12	41	ca1efe58-d28a-4bce-b850-9710ce2d7b5b	0	初始化数据	2026-03-22 21:43:05.976778	2026-03-22 21:43:05.976778
删除部门	3	3	module_system:dept:delete	\N	\N	\N	\N	\N	f	t	f	删除部门	null	f	12	42	394d42d0-3323-431a-9fcf-1c435eb51651	0	初始化数据	2026-03-22 21:43:05.976781	2026-03-22 21:43:05.976781
批量修改部门状态	3	4	module_system:dept:patch	\N	\N	\N	\N	\N	f	t	f	批量修改部门状态	null	f	12	43	eaf51d88-190d-426b-a359-00d8090f895f	0	初始化数据	2026-03-22 21:43:05.976784	2026-03-22 21:43:05.976784
详情部门	3	5	module_system:dept:detail	\N	\N	\N	\N	\N	f	t	f	详情部门	null	f	12	44	aedb848a-c8ba-4158-bf75-0f2349a3daba	0	初始化数据	2026-03-22 21:43:05.976787	2026-03-22 21:43:05.976787
查询部门	3	6	module_system:dept:query	\N	\N	\N	\N	\N	f	t	f	查询部门	null	f	12	45	3cc97ab4-e1db-4432-9efe-7eed02d7cc45	0	初始化数据	2026-03-22 21:43:05.97679	2026-03-22 21:43:05.97679
创建岗位	3	1	module_system:position:create	\N	\N	\N	\N	\N	f	t	f	创建岗位	null	f	13	46	c0fa5fcb-54e1-47fa-9dbb-d4a5ac7c2304	0	初始化数据	2026-03-22 21:43:05.976792	2026-03-22 21:43:05.976793
修改岗位	3	2	module_system:position:update	\N	\N	\N	\N	\N	f	t	f	修改岗位	null	f	13	47	78d5beb2-8eb9-4ae8-9c1b-752b6498f6e8	0	初始化数据	2026-03-22 21:43:05.976795	2026-03-22 21:43:05.976795
删除岗位	3	3	module_system:position:delete	\N	\N	\N	\N	\N	f	t	f	修改岗位	null	f	13	48	f6b9e93f-bc21-4207-a8ca-09ac09f862f3	0	初始化数据	2026-03-22 21:43:05.976798	2026-03-22 21:43:05.976798
批量修改岗位状态	3	4	module_system:position:patch	\N	\N	\N	\N	\N	f	t	f	批量修改岗位状态	null	f	13	49	d5a24b74-becc-4b1d-89a6-2a36b83458ca	0	初始化数据	2026-03-22 21:43:05.976801	2026-03-22 21:43:05.976801
岗位导出	3	5	module_system:position:export	\N	\N	\N	\N	\N	f	t	f	岗位导出	null	f	13	50	66d8166b-da43-40bf-8b8c-0db05d71cbb7	0	初始化数据	2026-03-22 21:43:05.976803	2026-03-22 21:43:05.976804
详情岗位	3	6	module_system:position:detail	\N	\N	\N	\N	\N	f	t	f	详情岗位	null	f	13	51	a0e7096e-df2c-4a0b-b3bd-7ed47edf4eba	0	初始化数据	2026-03-22 21:43:05.976806	2026-03-22 21:43:05.976807
查询岗位	3	7	module_system:position:query	\N	\N	\N	\N	\N	f	t	f	查询岗位	null	f	13	52	965cd675-63b6-45bf-9703-531b9dd35153	0	初始化数据	2026-03-22 21:43:05.976809	2026-03-22 21:43:05.976809
创建角色	3	1	module_system:role:create	\N	\N	\N	\N	\N	f	t	f	创建角色	null	f	14	53	06612c78-e297-4b30-91d2-4a556a4731d0	0	初始化数据	2026-03-22 21:43:05.976812	2026-03-22 21:43:05.976812
修改角色	3	2	module_system:role:update	\N	\N	\N	\N	\N	f	t	f	修改角色	null	f	14	54	d15ababf-3cf4-467f-94fd-638a8c98f838	0	初始化数据	2026-03-22 21:43:05.976815	2026-03-22 21:43:05.976815
删除角色	3	3	module_system:role:delete	\N	\N	\N	\N	\N	f	t	f	删除角色	null	f	14	55	65a2a301-623f-48cd-b9b8-76830361e785	0	初始化数据	2026-03-22 21:43:05.976818	2026-03-22 21:43:05.976818
批量修改角色状态	3	4	module_system:role:patch	\N	\N	\N	\N	\N	f	t	f	批量修改角色状态	null	f	14	56	a38a5cd9-ebc8-4ae2-b24d-3bc31796fe13	0	初始化数据	2026-03-22 21:43:05.97682	2026-03-22 21:43:05.976821
角色导出	3	5	module_system:role:export	\N	\N	\N	\N	\N	f	t	f	角色导出	null	f	14	57	1e0a6876-bce6-4e20-92dc-42d7442c97fb	0	初始化数据	2026-03-22 21:43:05.976823	2026-03-22 21:43:05.976824
详情角色	3	6	module_system:role:detail	\N	\N	\N	\N	\N	f	t	f	详情角色	null	f	14	58	59926ee1-3677-4055-9162-4013c756c189	0	初始化数据	2026-03-22 21:43:05.976826	2026-03-22 21:43:05.976826
查询角色	3	7	module_system:role:query	\N	\N	\N	\N	\N	f	t	f	查询角色	null	f	14	59	332cc688-2141-49bb-9802-9815ca551613	0	初始化数据	2026-03-22 21:43:05.976829	2026-03-22 21:43:05.976829
分配权限	3	8	module_system:role:permission	\N	\N	\N	\N	\N	f	t	f	分配权限	null	f	14	60	a1827623-7931-45ea-979b-734830ec7758	0	初始化数据	2026-03-22 21:43:05.976831	2026-03-22 21:43:05.976832
创建用户	3	1	module_system:user:create	\N	\N	\N	\N	\N	f	t	f	创建用户	null	f	15	61	78418cd8-eb93-4e2e-b3ac-d678555cf492	0	初始化数据	2026-03-22 21:43:05.976834	2026-03-22 21:43:05.976835
修改用户	3	2	module_system:user:update	\N	\N	\N	\N	\N	f	t	f	修改用户	null	f	15	62	f5496bc0-39f6-48b4-8f46-0eefabd6dfb3	0	初始化数据	2026-03-22 21:43:05.976837	2026-03-22 21:43:05.976837
删除用户	3	3	module_system:user:delete	\N	\N	\N	\N	\N	f	t	f	删除用户	null	f	15	63	46c63c3b-d721-43ea-92ea-d555e3f955e4	0	初始化数据	2026-03-22 21:43:05.97684	2026-03-22 21:43:05.97684
批量修改用户状态	3	4	module_system:user:patch	\N	\N	\N	\N	\N	f	t	f	批量修改用户状态	null	f	15	64	0b6e5450-da73-4c5e-9068-de4d1f375e1f	0	初始化数据	2026-03-22 21:43:05.976843	2026-03-22 21:43:05.976843
导出用户	3	5	module_system:user:export	\N	\N	\N	\N	\N	f	t	f	导出用户	null	f	15	65	45441a14-4010-4268-8ddf-b8e829f739ee	0	初始化数据	2026-03-22 21:43:05.976845	2026-03-22 21:43:05.976846
导入用户	3	6	module_system:user:import	\N	\N	\N	\N	\N	f	t	f	导入用户	null	f	15	66	3bcef7ed-6691-421c-b120-9f3163511bc3	0	初始化数据	2026-03-22 21:43:05.976848	2026-03-22 21:43:05.976849
下载用户导入模板	3	7	module_system:user:download	\N	\N	\N	\N	\N	f	t	f	下载用户导入模板	null	f	15	67	5d6b259f-c2bc-4d85-a5a9-60554f885514	0	初始化数据	2026-03-22 21:43:05.976851	2026-03-22 21:43:05.976851
详情用户	3	8	module_system:user:detail	\N	\N	\N	\N	\N	f	t	f	详情用户	null	f	15	68	559147fd-0e35-42f9-a915-5ff9debeb568	0	初始化数据	2026-03-22 21:43:05.976854	2026-03-22 21:43:05.976854
查询用户	3	9	module_system:user:query	\N	\N	\N	\N	\N	f	t	f	查询用户	null	f	15	69	93b4f2ae-3576-4a2d-9410-02e057686360	0	初始化数据	2026-03-22 21:43:05.976857	2026-03-22 21:43:05.976857
日志删除	3	1	module_system:log:delete	\N	\N	\N	\N	\N	f	t	f	日志删除	null	f	16	70	b4068c18-186e-4eb0-8f92-7ae820c27d3d	0	初始化数据	2026-03-22 21:43:05.97686	2026-03-22 21:43:05.97686
日志导出	3	2	module_system:log:export	\N	\N	\N	\N	\N	f	t	f	日志导出	null	f	16	71	404093ed-1651-4e19-955d-3b28f56c1dcd	0	初始化数据	2026-03-22 21:43:05.976862	2026-03-22 21:43:05.976863
日志详情	3	3	module_system:log:detail	\N	\N	\N	\N	\N	f	t	f	日志详情	null	f	16	72	edcb0dbd-929e-4782-8733-604fd0d6c49d	0	初始化数据	2026-03-22 21:43:05.976865	2026-03-22 21:43:05.976865
查询日志	3	4	module_system:log:query	\N	\N	\N	\N	\N	f	t	f	查询日志	null	f	16	73	ca921544-aa68-4da3-b96e-ca7425f387ec	0	初始化数据	2026-03-22 21:43:05.976868	2026-03-22 21:43:05.976868
公告创建	3	1	module_system:notice:create	\N	\N	\N	\N	\N	f	t	f	公告创建	null	f	17	74	87ec6a4c-e1c6-4396-b566-6fb75335f986	0	初始化数据	2026-03-22 21:43:05.976871	2026-03-22 21:43:05.976871
公告修改	3	2	module_system:notice:update	\N	\N	\N	\N	\N	f	t	f	修改用户	null	f	17	75	09820fb3-e7dc-4cf1-b2f1-f75a20752a80	0	初始化数据	2026-03-22 21:43:05.976874	2026-03-22 21:43:05.976874
公告删除	3	3	module_system:notice:delete	\N	\N	\N	\N	\N	f	t	f	公告删除	null	f	17	76	fd25b986-26a3-4dda-a117-ecc90ac75cbc	0	初始化数据	2026-03-22 21:43:05.976876	2026-03-22 21:43:05.976877
公告导出	3	4	module_system:notice:export	\N	\N	\N	\N	\N	f	t	f	公告导出	null	f	17	77	70d53a34-a3e6-49bc-aa0b-755eac643e5f	0	初始化数据	2026-03-22 21:43:05.976879	2026-03-22 21:43:05.976879
公告批量修改状态	3	5	module_system:notice:patch	\N	\N	\N	\N	\N	f	t	f	公告批量修改状态	null	f	17	78	3512224d-7d64-4085-ad1f-f976fbcaf782	0	初始化数据	2026-03-22 21:43:05.976882	2026-03-22 21:43:05.976882
公告详情	3	6	module_system:notice:detail	\N	\N	\N	\N	\N	f	t	f	公告详情	null	f	17	79	d6e9c490-6181-44cf-a554-c81c89e88fa0	0	初始化数据	2026-03-22 21:43:05.976884	2026-03-22 21:43:05.976885
查询公告	3	5	module_system:notice:query	\N	\N	\N	\N	\N	f	t	f	查询公告	null	f	17	80	31000118-1fae-422c-b3a9-609bf65094cd	0	初始化数据	2026-03-22 21:43:05.976887	2026-03-22 21:43:05.976888
创建参数	3	1	module_system:param:create	\N	\N	\N	\N	\N	f	t	f	创建参数	null	f	18	81	7e943782-03ed-4773-9033-7e8ab14a2af1	0	初始化数据	2026-03-22 21:43:05.97689	2026-03-22 21:43:05.97689
修改参数	3	2	module_system:param:update	\N	\N	\N	\N	\N	f	t	f	修改参数	null	f	18	82	15550ee4-8772-46a3-96a3-7d1ad975959b	0	初始化数据	2026-03-22 21:43:05.976893	2026-03-22 21:43:05.976893
删除参数	3	3	module_system:param:delete	\N	\N	\N	\N	\N	f	t	f	删除参数	null	f	18	83	8756caea-c1e4-42bf-bd15-444f5a0c68ce	0	初始化数据	2026-03-22 21:43:05.976898	2026-03-22 21:43:05.976898
导出参数	3	4	module_system:param:export	\N	\N	\N	\N	\N	f	t	f	导出参数	null	f	18	84	ebbc32c4-0237-4beb-9f50-8a80d25c1848	0	初始化数据	2026-03-22 21:43:05.976901	2026-03-22 21:43:05.976901
参数上传	3	5	module_system:param:upload	\N	\N	\N	\N	\N	f	t	f	参数上传	null	f	18	85	dd9a7466-433d-40f4-8720-4f50345ae717	0	初始化数据	2026-03-22 21:43:05.976904	2026-03-22 21:43:05.976904
参数详情	3	6	module_system:param:detail	\N	\N	\N	\N	\N	f	t	f	参数详情	null	f	18	86	477bb50d-d87f-4698-9cf9-3d90a90a625e	0	初始化数据	2026-03-22 21:43:05.976907	2026-03-22 21:43:05.976907
查询参数	3	7	module_system:param:query	\N	\N	\N	\N	\N	f	t	f	查询参数	null	f	18	87	6101f458-4786-40ce-879f-ea8ace435687	0	初始化数据	2026-03-22 21:43:05.97691	2026-03-22 21:43:05.97691
创建字典类型	3	1	module_system:dict_type:create	\N	\N	\N	\N	\N	f	t	f	创建字典类型	null	f	19	88	a09b9442-9a29-4130-af0f-c33b305c9788	0	初始化数据	2026-03-22 21:43:05.976912	2026-03-22 21:43:05.976913
修改字典类型	3	2	module_system:dict_type:update	\N	\N	\N	\N	\N	f	t	f	修改字典类型	null	f	19	89	ec2420d2-2436-4110-80ec-07d5cf9740c8	0	初始化数据	2026-03-22 21:43:05.976915	2026-03-22 21:43:05.976915
删除字典类型	3	3	module_system:dict_type:delete	\N	\N	\N	\N	\N	f	t	f	删除字典类型	null	f	19	90	6e1205aa-7aa3-473f-aded-c7f824891695	0	初始化数据	2026-03-22 21:43:05.976918	2026-03-22 21:43:05.976918
导出字典类型	3	4	module_system:dict_type:export	\N	\N	\N	\N	\N	f	t	f	导出字典类型	null	f	19	91	419ebcef-c163-4f30-96be-ca6f4efe6722	0	初始化数据	2026-03-22 21:43:05.976921	2026-03-22 21:43:05.976921
批量修改字典状态	3	5	module_system:dict_type:patch	\N	\N	\N	\N	\N	f	t	f	导出字典类型	null	f	19	92	60c226c8-d535-4e53-8a59-fff1b871a26a	0	初始化数据	2026-03-22 21:43:05.976923	2026-03-22 21:43:05.976924
字典数据查询	3	6	module_system:dict_data:query	\N	\N	\N	\N	\N	f	t	f	字典数据查询	null	f	19	93	0d624a1c-5258-4a1e-9a62-448bdd8452df	0	初始化数据	2026-03-22 21:43:05.976926	2026-03-22 21:43:05.976927
创建字典数据	3	7	module_system:dict_data:create	\N	\N	\N	\N	\N	f	t	f	创建字典数据	null	f	19	94	4d682e2f-4491-4a98-b2b7-8aa868f9ca29	0	初始化数据	2026-03-22 21:43:05.976929	2026-03-22 21:43:05.976929
修改字典数据	3	8	module_system:dict_data:update	\N	\N	\N	\N	\N	f	t	f	修改字典数据	null	f	19	95	e96a932d-f0b9-408b-b608-ea0f6918dfd4	0	初始化数据	2026-03-22 21:43:05.976932	2026-03-22 21:43:05.976932
删除字典数据	3	9	module_system:dict_data:delete	\N	\N	\N	\N	\N	f	t	f	删除字典数据	null	f	19	96	c93e2f49-1858-4240-bd1d-e94a6e1081d6	0	初始化数据	2026-03-22 21:43:05.976935	2026-03-22 21:43:05.976935
导出字典数据	3	10	module_system:dict_data:export	\N	\N	\N	\N	\N	f	t	f	导出字典数据	null	f	19	97	8e3c461c-f6ff-45e1-8174-8c304720e915	0	初始化数据	2026-03-22 21:43:05.976937	2026-03-22 21:43:05.976938
批量修改字典数据状态	3	11	module_system:dict_data:patch	\N	\N	\N	\N	\N	f	t	f	批量修改字典数据状态	null	f	19	98	9060a8ab-05e1-45b9-8622-1bc296ce2700	0	初始化数据	2026-03-22 21:43:05.97694	2026-03-22 21:43:05.97694
详情字典类型	3	12	module_system:dict_type:detail	\N	\N	\N	\N	\N	f	t	f	详情字典类型	null	f	19	99	224043af-2899-436d-9cb0-c9775a9f6f61	0	初始化数据	2026-03-22 21:43:05.976943	2026-03-22 21:43:05.976943
查询字典类型	3	13	module_system:dict_type:query	\N	\N	\N	\N	\N	f	t	f	查询字典类型	null	f	19	100	081f9089-c5c6-4cd1-ad2b-29533c095075	0	初始化数据	2026-03-22 21:43:05.976946	2026-03-22 21:43:05.976946
详情字典数据	3	14	module_system:dict_data:detail	\N	\N	\N	\N	\N	f	t	f	详情字典数据	null	f	19	101	cf05c9c8-95b5-402f-944d-f09123f6af8f	0	初始化数据	2026-03-22 21:43:05.976948	2026-03-22 21:43:05.976949
在线用户强制下线	3	1	module_monitor:online:delete	\N	\N	\N	\N	\N	f	t	f	在线用户强制下线	null	f	20	102	7a25dacc-d525-4896-bba4-1090020596c2	0	初始化数据	2026-03-22 21:43:05.976951	2026-03-22 21:43:05.976951
清除缓存	3	1	module_monitor:cache:delete	\N	\N	\N	\N	\N	f	t	f	清除缓存	null	f	22	103	32cf7e60-b6ce-4822-9c2c-cdf74a21e99e	0	初始化数据	2026-03-22 21:43:05.976954	2026-03-22 21:43:05.976954
文件上传	3	1	module_monitor:resource:upload	\N	\N	\N	\N	\N	f	t	f	文件上传	null	f	23	104	618b8aab-2c09-4c12-bf0c-32e7d05c8aa0	0	初始化数据	2026-03-22 21:43:05.976957	2026-03-22 21:43:05.976957
文件下载	3	2	module_monitor:resource:download	\N	\N	\N	\N	\N	f	t	f	文件下载	null	f	23	105	b9dffa25-bdc1-4d9e-a51a-60e54c0995dc	0	初始化数据	2026-03-22 21:43:05.976959	2026-03-22 21:43:05.97696
文件删除	3	3	module_monitor:resource:delete	\N	\N	\N	\N	\N	f	t	f	文件删除	null	f	23	106	c888a1ea-f756-4415-b1eb-e855192e53fb	0	初始化数据	2026-03-22 21:43:05.976962	2026-03-22 21:43:05.976962
文件移动	3	4	module_monitor:resource:move	\N	\N	\N	\N	\N	f	t	f	文件移动	null	f	23	107	5b116c0d-9c5e-4bf4-a022-9701b71b201a	0	初始化数据	2026-03-22 21:43:05.976965	2026-03-22 21:43:05.976965
文件复制	3	5	module_monitor:resource:copy	\N	\N	\N	\N	\N	f	t	f	文件复制	null	f	23	108	c13a04ff-632d-4833-9acc-f09dbcf520c4	0	初始化数据	2026-03-22 21:43:05.976968	2026-03-22 21:43:05.976968
文件重命名	3	6	module_monitor:resource:rename	\N	\N	\N	\N	\N	f	t	f	文件重命名	null	f	23	109	68698867-586b-4323-ad82-af3c7f9d4d72	0	初始化数据	2026-03-22 21:43:05.97697	2026-03-22 21:43:05.976971
创建目录	3	7	module_monitor:resource:create_dir	\N	\N	\N	\N	\N	f	t	f	创建目录	null	f	23	110	30fc3f17-26b7-4867-878c-52a4f8a34f13	0	初始化数据	2026-03-22 21:43:05.976973	2026-03-22 21:43:05.976974
导出文件列表	3	9	module_monitor:resource:export	\N	\N	\N	\N	\N	f	t	f	导出文件列表	null	f	23	111	42548be7-1942-48e2-8dec-d31d8f119c54	0	初始化数据	2026-03-22 21:43:05.976976	2026-03-22 21:43:05.976976
查询代码生成业务表列表	3	1	module_generator:gencode:query	\N	\N	\N	\N	\N	f	t	f	查询代码生成业务表列表	null	f	27	112	434b35f7-9f4a-4343-bd42-ec863705a13c	0	查询代码生成业务表列表	2026-03-22 21:43:05.976979	2026-03-22 21:43:05.976979
创建表结构	3	2	module_generator:gencode:create	\N	\N	\N	\N	\N	f	t	f	创建表结构	null	f	27	113	ace26951-0126-429e-90e7-d3205587f0e0	0	创建表结构	2026-03-22 21:43:05.976982	2026-03-22 21:43:05.976982
编辑业务表信息	3	3	module_generator:gencode:update	\N	\N	\N	\N	\N	f	t	f	编辑业务表信息	null	f	27	114	c283f18e-2f04-4912-a4a2-b06e0330a343	0	编辑业务表信息	2026-03-22 21:43:05.976984	2026-03-22 21:43:05.976985
删除业务表信息	3	4	module_generator:gencode:delete	\N	\N	\N	\N	\N	f	t	f	删除业务表信息	null	f	27	115	5700dccd-dfd6-4645-b734-1cd2558d575f	0	删除业务表信息	2026-03-22 21:43:05.976987	2026-03-22 21:43:05.976987
导入表结构	3	5	module_generator:gencode:import	\N	\N	\N	\N	\N	f	t	f	导入表结构	null	f	27	116	c0a88b55-b9aa-4016-aae5-51ed1f379bf7	0	导入表结构	2026-03-22 21:43:05.97699	2026-03-22 21:43:05.97699
批量生成代码	3	6	module_generator:gencode:operate	\N	\N	\N	\N	\N	f	t	f	批量生成代码	null	f	27	117	488d3a39-2e18-4722-a5c6-bc71f2c2ad59	0	批量生成代码	2026-03-22 21:43:05.976993	2026-03-22 21:43:05.976993
生成代码到指定路径	3	7	module_generator:gencode:code	\N	\N	\N	\N	\N	f	t	f	生成代码到指定路径	null	f	27	118	3b7c84dc-edbe-4d15-9591-b20e975efe94	0	生成代码到指定路径	2026-03-22 21:43:05.976995	2026-03-22 21:43:05.976996
查询数据库表列表	3	8	module_generator:dblist:query	\N	\N	\N	\N	\N	f	t	f	查询数据库表列表	null	f	27	119	4bee1cc9-8e58-4e47-9c03-14f87fe8b099	0	查询数据库表列表	2026-03-22 21:43:05.976998	2026-03-22 21:43:05.976998
同步数据库	3	9	module_generator:db:sync	\N	\N	\N	\N	\N	f	t	f	同步数据库	null	f	27	120	d9d7749d-2f50-4247-bb63-7d54670e3561	0	同步数据库	2026-03-22 21:43:05.977001	2026-03-22 21:43:05.977001
创建应用	3	1	module_application:myapp:create	\N	\N	\N	\N	\N	f	t	f	创建应用	null	f	28	121	bfa004dd-fc2a-40d1-a621-f93e3582d138	0	初始化数据	2026-03-22 21:43:05.977003	2026-03-22 21:43:05.977004
修改应用	3	2	module_application:myapp:update	\N	\N	\N	\N	\N	f	t	f	修改应用	null	f	28	122	c7bca474-800a-4326-a000-b16efc41abda	0	初始化数据	2026-03-22 21:43:05.977006	2026-03-22 21:43:05.977006
删除应用	3	3	module_application:myapp:delete	\N	\N	\N	\N	\N	f	t	f	删除应用	null	f	28	123	112ae8b1-eb22-40a0-8036-cd1cf03df48d	0	初始化数据	2026-03-22 21:43:05.977009	2026-03-22 21:43:05.977009
批量修改应用状态	3	4	module_application:myapp:patch	\N	\N	\N	\N	\N	f	t	f	批量修改应用状态	null	f	28	124	cc01dbb4-1551-42a0-a138-698230cd11bd	0	初始化数据	2026-03-22 21:43:05.977012	2026-03-22 21:43:05.977012
详情应用	3	5	module_application:myapp:detail	\N	\N	\N	\N	\N	f	t	f	详情应用	null	f	28	125	64317a64-9489-4bca-9342-fb3df8079dfc	0	初始化数据	2026-03-22 21:43:05.977014	2026-03-22 21:43:05.977015
查询应用	3	6	module_application:myapp:query	\N	\N	\N	\N	\N	f	t	f	查询应用	null	f	28	126	177399c4-fa1c-48fd-820d-203201aa71d3	0	初始化数据	2026-03-22 21:43:05.977017	2026-03-22 21:43:05.977018
AI对话	3	1	module_ai:chat:ws	\N	\N	\N	\N	\N	f	t	f	AI对话	null	f	29	127	d0fdc1d5-ef96-4435-afcc-7e50e887bad2	0	AI对话	2026-03-22 21:43:05.97702	2026-03-22 21:43:05.97702
查询会话	3	2	module_ai:chat:query	\N	\N	\N	\N	\N	f	t	f	查询会话	null	f	29	128	83cc1124-3f2c-4347-b4a8-43a02c2ec9b1	0	查询会话	2026-03-22 21:43:05.977024	2026-03-22 21:43:05.977024
会话详情	3	3	module_ai:chat:detail	\N	\N	\N	\N	\N	f	t	f	会话详情	null	f	29	129	a9f784c6-b58e-4f9d-aedb-afd723c9e7a9	0	会话详情	2026-03-22 21:43:05.977027	2026-03-22 21:43:05.977027
创建会话	3	4	module_ai:chat:create	\N	\N	\N	\N	\N	f	t	f	创建会话	null	f	29	130	fbf44da6-6945-485a-899c-de712b508394	0	创建会话	2026-03-22 21:43:05.97703	2026-03-22 21:43:05.97703
更新会话	3	5	module_ai:chat:update	\N	\N	\N	\N	\N	f	t	f	更新会话	null	f	29	131	0449e59f-bb96-46fa-bb2a-3851697b157e	0	更新会话	2026-03-22 21:43:05.977033	2026-03-22 21:43:05.977033
删除会话	3	6	module_ai:chat:delete	\N	\N	\N	\N	\N	f	t	f	删除会话	null	f	29	132	e83b2210-1139-41bc-b45e-3368f7734d69	0	删除会话	2026-03-22 21:43:05.977035	2026-03-22 21:43:05.977036
查询会话记忆	3	1	module_ai:chat:query	\N	\N	\N	\N	\N	f	t	f	查询会话记忆	null	f	30	133	931463e9-d38b-4d49-96a2-ec06e7cfe79c	0	查询会话记忆	2026-03-22 21:43:05.977038	2026-03-22 21:43:05.977038
会话记忆详情	3	2	module_ai:chat:detail	\N	\N	\N	\N	\N	f	t	f	会话记忆详情	null	f	30	134	ff91ccd5-84dd-44ce-b2c0-664412616095	0	会话记忆详情	2026-03-22 21:43:05.977041	2026-03-22 21:43:05.977041
删除会话记忆	3	3	module_ai:chat:delete	\N	\N	\N	\N	\N	f	t	f	删除会话记忆	null	f	30	135	1fa7cf63-4fb7-443c-bc59-cd1745145125	0	删除会话记忆	2026-03-22 21:43:05.977044	2026-03-22 21:43:05.977045
查询调度器	3	1	module_task:job:query	\N	\N	\N	\N	\N	f	t	f	查询调度器	null	f	31	136	eb3ab1fa-7e68-472e-86f0-7cc2bdee00f9	0	查询调度器	2026-03-22 21:43:05.977048	2026-03-22 21:43:05.977048
控制调度器	3	2	module_task:job:scheduler	\N	\N	\N	\N	\N	f	t	f	控制调度器	null	f	31	137	82ee54e1-3447-4015-980e-f665a66f8b6b	0	控制调度器	2026-03-22 21:43:05.977052	2026-03-22 21:43:05.977052
操作任务	3	3	module_task:job:task	\N	\N	\N	\N	\N	f	t	f	操作任务	null	f	31	138	5f116a2a-a065-4b1d-9f64-15c5d52f13d4	0	操作任务	2026-03-22 21:43:05.977055	2026-03-22 21:43:05.977056
删除执行日志	3	4	module_task:job:delete	\N	\N	\N	\N	\N	f	t	f	删除执行日志	null	f	31	139	b8ab9f65-7494-461b-a069-402148e859f0	0	删除执行日志	2026-03-22 21:43:05.977059	2026-03-22 21:43:05.97706
详情执行日志	3	5	module_task:job:detail	\N	\N	\N	\N	\N	f	t	f	详情执行日志	null	f	31	140	39c1ae87-e1e8-4b4d-8937-2041c510ecc9	0	详情执行日志	2026-03-22 21:43:05.977063	2026-03-22 21:43:05.977063
创建节点	3	1	module_task:node:create	\N	\N	\N	\N	\N	f	t	f	创建节点	null	f	32	141	7798a653-f4b1-4192-add2-f28fdc77ca33	0	创建节点	2026-03-22 21:43:05.977066	2026-03-22 21:43:05.977066
调试节点	3	2	module_task:node:execute	\N	\N	\N	\N	\N	f	t	f	调试节点	null	f	32	142	72c0de5c-6914-44c9-8c2b-6f6328bbd37c	0	调试节点	2026-03-22 21:43:05.977069	2026-03-22 21:43:05.977069
修改节点	3	3	module_task:node:update	\N	\N	\N	\N	\N	f	t	f	修改节点	null	f	32	143	27b1b5eb-f5ce-4aa2-afd2-c54cd34995b5	0	修改节点	2026-03-22 21:43:05.977072	2026-03-22 21:43:05.977072
删除节点	3	4	module_task:node:delete	\N	\N	\N	\N	\N	f	t	f	删除节点	null	f	32	144	1f56d598-9ba1-4da7-8666-fa66c6abc10d	0	删除节点	2026-03-22 21:43:05.977075	2026-03-22 21:43:05.977075
详情节点	3	5	module_task:node:detail	\N	\N	\N	\N	\N	f	t	f	详情节点	null	f	32	145	d3afaabe-41d9-4137-b9dc-6bb51b11a774	0	详情节点	2026-03-22 21:43:05.977078	2026-03-22 21:43:05.977078
查询节点	3	6	module_task:node:query	\N	\N	\N	\N	\N	f	t	f	查询节点	null	f	32	146	84c251c9-e0ff-4e69-a5c2-1ddf6f4f79be	0	查询节点	2026-03-22 21:43:05.977081	2026-03-22 21:43:05.977081
创建示例	3	1	module_example:demo:create	\N	\N	\N	\N	\N	f	t	f	创建示例	null	f	33	147	90bc5b22-7ddd-4125-8030-ce6eedf73d83	0	初始化数据	2026-03-22 21:43:05.977084	2026-03-22 21:43:05.977084
更新示例	3	2	module_example:demo:update	\N	\N	\N	\N	\N	f	t	f	更新示例	null	f	33	148	0dd2d3d0-dc33-4df7-8b13-95bf3a3279e3	0	初始化数据	2026-03-22 21:43:05.977086	2026-03-22 21:43:05.977087
删除示例	3	3	module_example:demo:delete	\N	\N	\N	\N	\N	f	t	f	删除示例	null	f	33	149	8dc86a99-4473-4538-9f68-36852339f783	0	初始化数据	2026-03-22 21:43:05.977089	2026-03-22 21:43:05.97709
批量修改示例状态	3	4	module_example:demo:patch	\N	\N	\N	\N	\N	f	t	f	批量修改示例状态	null	f	33	150	fdb72e46-1492-47da-ab1b-a62e927ce1a2	0	初始化数据	2026-03-22 21:43:05.977092	2026-03-22 21:43:05.977093
导出示例	3	5	module_example:demo:export	\N	\N	\N	\N	\N	f	t	f	导出示例	null	f	33	151	9f1b0f95-3d23-4e0c-aa8f-761650d2e660	0	初始化数据	2026-03-22 21:43:05.977096	2026-03-22 21:43:05.977096
导入示例	3	6	module_example:demo:import	\N	\N	\N	\N	\N	f	t	f	导入示例	null	f	33	152	dcdd1979-2137-4503-be2c-3aa0abb679d8	0	初始化数据	2026-03-22 21:43:05.9771	2026-03-22 21:43:05.9771
下载导入示例模版	3	7	module_example:demo:download	\N	\N	\N	\N	\N	f	t	f	下载导入示例模版	null	f	33	153	63f39f2c-78cb-4613-8e2a-bc5198bd2ef5	0	初始化数据	2026-03-22 21:43:05.977104	2026-03-22 21:43:05.977104
详情示例	3	8	module_example:demo:detail	\N	\N	\N	\N	\N	f	t	f	详情示例	null	f	33	154	8afdf1dc-8604-46f3-a0e5-32a616f8a234	0	初始化数据	2026-03-22 21:43:05.977108	2026-03-22 21:43:05.977108
查询示例	3	9	module_example:demo:query	\N	\N	\N	\N	\N	f	t	f	查询示例	null	f	33	155	65c286ec-cfe1-4ea2-b888-d1cc2c6f3537	0	初始化数据	2026-03-22 21:43:05.977112	2026-03-22 21:43:05.977112
\.


--
-- Data for Name: sys_notice; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_notice (notice_title, notice_type, notice_content, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: sys_param; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_param (config_name, config_key, config_value, config_type, id, uuid, status, description, created_time, updated_time) FROM stdin;
网站名称	sys_web_title	FastApiAdmin	t	1	0c91ca52-00ff-45d5-8493-30fd630c994e	0	初始化数据	2026-03-22 21:43:05.985228	2026-03-22 21:43:05.98523
网站描述	sys_web_description	FastApiAdmin 是完全开源的权限管理系统	t	2	9a0ecb98-722e-4f39-babd-940a142b9dc4	0	初始化数据	2026-03-22 21:43:05.985233	2026-03-22 21:43:05.985234
网页图标	sys_web_favicon	https://service.fastapiadmin.com/api/v1/static/image/favicon.png	t	3	f11dd999-e703-480c-9807-4be22bd867f8	0	初始化数据	2026-03-22 21:43:05.985236	2026-03-22 21:43:05.985237
网站Logo	sys_web_logo	https://service.fastapiadmin.com/api/v1/static/image/logo.png	t	4	7c312622-9adc-4178-861d-2c893d1404e9	0	初始化数据	2026-03-22 21:43:05.985239	2026-03-22 21:43:05.98524
登录背景	sys_login_background	https://service.fastapiadmin.com/api/v1/static/image/background.svg	t	5	88161bf0-4f0d-4d54-86fe-e6b0504355a9	0	初始化数据	2026-03-22 21:43:05.985242	2026-03-22 21:43:05.985242
版权信息	sys_web_copyright	Copyright © 2025-2026 service.fastapiadmin.com 版权所有	t	6	07e4cf74-1e63-4dd0-815d-8e1fab6a0fcf	0	初始化数据	2026-03-22 21:43:05.985245	2026-03-22 21:43:05.985245
备案信息	sys_keep_record	陕ICP备2025069493号-1	t	7	6de94ed4-03bf-4b99-9914-464f14da00e0	0	初始化数据	2026-03-22 21:43:05.985248	2026-03-22 21:43:05.985248
帮助文档	sys_help_doc	https://service.fastapiadmin.com	t	8	a580c6f1-6983-4d53-a6de-caff1fa0f8fd	0	初始化数据	2026-03-22 21:43:05.985251	2026-03-22 21:43:05.985251
隐私政策	sys_web_privacy	https://github.com/fastapiadmin/FastapiAdmin/blob/master/LICENSE	t	9	33e9c62a-52df-41db-8693-e65c761b7862	0	初始化数据	2026-03-22 21:43:05.985253	2026-03-22 21:43:05.985254
用户协议	sys_web_clause	https://github.com/fastapiadmin/FastapiAdmin/blob/master/LICENSE	t	10	aa44d50f-7b63-4859-ba52-5eab38ee17c6	0	初始化数据	2026-03-22 21:43:05.985256	2026-03-22 21:43:05.985257
源码代码	sys_git_code	https://github.com/fastapiadmin/FastapiAdmin.git	t	11	45ca17ab-db72-49ee-8897-04168afb7214	0	初始化数据	2026-03-22 21:43:05.985259	2026-03-22 21:43:05.985259
项目版本	sys_web_version	2.0.0	t	12	a0a6ecc5-01b2-4b20-9ff8-f91d36564d59	0	初始化数据	2026-03-22 21:43:05.985262	2026-03-22 21:43:05.985262
演示模式启用	demo_enable	false	t	13	20015cde-7e2e-4638-a2ae-a27505cc5adc	0	初始化数据	2026-03-22 21:43:05.985265	2026-03-22 21:43:05.985265
演示访问IP白名单	ip_white_list	["127.0.0.1"]	t	14	fe102578-d556-4bd7-9a29-c0984b6e9699	0	初始化数据	2026-03-22 21:43:05.985267	2026-03-22 21:43:05.985268
接口白名单	white_api_list_path	["/api/v1/system/auth/login", "/api/v1/system/auth/token/refresh", "/api/v1/system/auth/captcha/get", "/api/v1/system/auth/logout", "/api/v1/system/config/info", "/api/v1/system/user/current/info", "/api/v1/system/notice/available", "/api/v1/system/auth/auto-login/users", "/api/v1/system/auth/auto-login/token", "/api/v1/system/auth/auto-login"]	t	15	f9d692c5-1eb2-466b-9f73-8a7de2346b0c	0	初始化数据	2026-03-22 21:43:05.98527	2026-03-22 21:43:05.985271
访问IP黑名单	ip_black_list	[]	t	16	c03ae4f0-e77b-43db-a3c3-1848d7111ff8	0	初始化数据	2026-03-22 21:43:05.985273	2026-03-22 21:43:05.985273
\.


--
-- Data for Name: sys_position; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_position (name, "order", id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Data for Name: sys_role; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_role (name, code, "order", data_scope, id, uuid, status, description, created_time, updated_time) FROM stdin;
管理员角色	ADMIN	1	4	1	7e82ad00-45ea-4e92-a99f-4c70dc223f7e	0	初始化角色	2026-03-22 21:43:05.990438	2026-03-22 21:43:05.990439
\.


--
-- Data for Name: sys_role_depts; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_role_depts (role_id, dept_id) FROM stdin;
\.


--
-- Data for Name: sys_role_menus; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_role_menus (role_id, menu_id) FROM stdin;
\.


--
-- Data for Name: sys_user; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_user (username, password, name, mobile, email, gender, avatar, is_superuser, last_login, gitee_login, github_login, wx_login, qq_login, dept_id, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
admin	$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa	超级管理员	\N	\N	0	https://service.fastapiadmin.com/api/v1/static/image/avatar.png	t	\N	\N	\N	\N	\N	1	1	bfb44036-9422-4d86-9db1-88b44b3cc618	0	超级管理员	2026-03-22 21:43:06.001432	2026-03-22 21:43:06.001432	\N	\N
\.


--
-- Data for Name: sys_user_positions; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_user_positions (user_id, position_id) FROM stdin;
\.


--
-- Data for Name: sys_user_roles; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.sys_user_roles (user_id, role_id) FROM stdin;
1	1
\.


--
-- Data for Name: task_job; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.task_job (job_id, job_name, trigger_type, status, next_run_time, job_state, result, error, id, uuid, description, created_time, updated_time) FROM stdin;
\.


--
-- Data for Name: task_node; Type: TABLE DATA; Schema: public; Owner: root
--

COPY public.task_node (name, code, jobstore, executor, trigger, trigger_args, func, args, kwargs, "coalesce", max_instances, start_date, end_date, id, uuid, status, description, created_time, updated_time, created_id, updated_id) FROM stdin;
\.


--
-- Name: app_myapp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.app_myapp_id_seq', 1, false);


--
-- Name: gen_demo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.gen_demo_id_seq', 1, false);


--
-- Name: gen_table_column_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.gen_table_column_id_seq', 1, false);


--
-- Name: gen_table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.gen_table_id_seq', 1, false);


--
-- Name: sys_dept_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_dept_id_seq', 1, true);


--
-- Name: sys_dict_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_dict_data_id_seq', 34, true);


--
-- Name: sys_dict_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_dict_type_id_seq', 10, true);


--
-- Name: sys_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_log_id_seq', 1, false);


--
-- Name: sys_menu_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_menu_id_seq', 155, true);


--
-- Name: sys_notice_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_notice_id_seq', 1, false);


--
-- Name: sys_param_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_param_id_seq', 16, true);


--
-- Name: sys_position_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_position_id_seq', 1, false);


--
-- Name: sys_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_role_id_seq', 1, true);


--
-- Name: sys_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.sys_user_id_seq', 1, true);


--
-- Name: task_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.task_job_id_seq', 1, false);


--
-- Name: task_node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.task_node_id_seq', 1, false);


--
-- Name: agno_schema_versions agno_schema_versions_pkey; Type: CONSTRAINT; Schema: ai; Owner: root
--

ALTER TABLE ONLY ai.agno_schema_versions
    ADD CONSTRAINT agno_schema_versions_pkey PRIMARY KEY (table_name);


--
-- Name: agno_sessions agno_sessions_pkey; Type: CONSTRAINT; Schema: ai; Owner: root
--

ALTER TABLE ONLY ai.agno_sessions
    ADD CONSTRAINT agno_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: app_myapp app_myapp_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.app_myapp
    ADD CONSTRAINT app_myapp_pkey PRIMARY KEY (id);


--
-- Name: apscheduler_jobs apscheduler_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.apscheduler_jobs
    ADD CONSTRAINT apscheduler_jobs_pkey PRIMARY KEY (id);


--
-- Name: gen_demo gen_demo_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_demo
    ADD CONSTRAINT gen_demo_pkey PRIMARY KEY (id);


--
-- Name: gen_table_column gen_table_column_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table_column
    ADD CONSTRAINT gen_table_column_pkey PRIMARY KEY (id);


--
-- Name: gen_table gen_table_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table
    ADD CONSTRAINT gen_table_pkey PRIMARY KEY (id);


--
-- Name: sys_dept sys_dept_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dept
    ADD CONSTRAINT sys_dept_pkey PRIMARY KEY (id);


--
-- Name: sys_dict_data sys_dict_data_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_data
    ADD CONSTRAINT sys_dict_data_pkey PRIMARY KEY (id);


--
-- Name: sys_dict_type sys_dict_type_dict_type_key; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_type
    ADD CONSTRAINT sys_dict_type_dict_type_key UNIQUE (dict_type);


--
-- Name: sys_dict_type sys_dict_type_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_type
    ADD CONSTRAINT sys_dict_type_pkey PRIMARY KEY (id);


--
-- Name: sys_log sys_log_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_log
    ADD CONSTRAINT sys_log_pkey PRIMARY KEY (id);


--
-- Name: sys_menu sys_menu_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_menu
    ADD CONSTRAINT sys_menu_pkey PRIMARY KEY (id);


--
-- Name: sys_notice sys_notice_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_notice
    ADD CONSTRAINT sys_notice_pkey PRIMARY KEY (id);


--
-- Name: sys_param sys_param_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_param
    ADD CONSTRAINT sys_param_pkey PRIMARY KEY (id);


--
-- Name: sys_position sys_position_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_position
    ADD CONSTRAINT sys_position_pkey PRIMARY KEY (id);


--
-- Name: sys_role_depts sys_role_depts_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_depts
    ADD CONSTRAINT sys_role_depts_pkey PRIMARY KEY (role_id, dept_id);


--
-- Name: sys_role_menus sys_role_menus_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_menus
    ADD CONSTRAINT sys_role_menus_pkey PRIMARY KEY (role_id, menu_id);


--
-- Name: sys_role sys_role_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role
    ADD CONSTRAINT sys_role_pkey PRIMARY KEY (id);


--
-- Name: sys_user sys_user_email_key; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_email_key UNIQUE (email);


--
-- Name: sys_user sys_user_mobile_key; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_mobile_key UNIQUE (mobile);


--
-- Name: sys_user sys_user_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_pkey PRIMARY KEY (id);


--
-- Name: sys_user_positions sys_user_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_positions
    ADD CONSTRAINT sys_user_positions_pkey PRIMARY KEY (user_id, position_id);


--
-- Name: sys_user_roles sys_user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_roles
    ADD CONSTRAINT sys_user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: sys_user sys_user_username_key; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_username_key UNIQUE (username);


--
-- Name: task_job task_job_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_job
    ADD CONSTRAINT task_job_pkey PRIMARY KEY (id);


--
-- Name: task_node task_node_code_key; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_node
    ADD CONSTRAINT task_node_code_key UNIQUE (code);


--
-- Name: task_node task_node_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_node
    ADD CONSTRAINT task_node_pkey PRIMARY KEY (id);


--
-- Name: idx_agno_schema_versions_created_at; Type: INDEX; Schema: ai; Owner: root
--

CREATE INDEX idx_agno_schema_versions_created_at ON ai.agno_schema_versions USING btree (created_at);


--
-- Name: idx_agno_sessions_created_at; Type: INDEX; Schema: ai; Owner: root
--

CREATE INDEX idx_agno_sessions_created_at ON ai.agno_sessions USING btree (created_at);


--
-- Name: idx_agno_sessions_session_type; Type: INDEX; Schema: ai; Owner: root
--

CREATE INDEX idx_agno_sessions_session_type ON ai.agno_sessions USING btree (session_type);


--
-- Name: ix_app_myapp_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_created_id ON public.app_myapp USING btree (created_id);


--
-- Name: ix_app_myapp_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_created_time ON public.app_myapp USING btree (created_time);


--
-- Name: ix_app_myapp_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_id ON public.app_myapp USING btree (id);


--
-- Name: ix_app_myapp_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_status ON public.app_myapp USING btree (status);


--
-- Name: ix_app_myapp_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_updated_id ON public.app_myapp USING btree (updated_id);


--
-- Name: ix_app_myapp_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_app_myapp_updated_time ON public.app_myapp USING btree (updated_time);


--
-- Name: ix_app_myapp_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_app_myapp_uuid ON public.app_myapp USING btree (uuid);


--
-- Name: ix_apscheduler_jobs_next_run_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_apscheduler_jobs_next_run_time ON public.apscheduler_jobs USING btree (next_run_time);


--
-- Name: ix_gen_demo_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_created_id ON public.gen_demo USING btree (created_id);


--
-- Name: ix_gen_demo_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_created_time ON public.gen_demo USING btree (created_time);


--
-- Name: ix_gen_demo_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_id ON public.gen_demo USING btree (id);


--
-- Name: ix_gen_demo_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_status ON public.gen_demo USING btree (status);


--
-- Name: ix_gen_demo_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_updated_id ON public.gen_demo USING btree (updated_id);


--
-- Name: ix_gen_demo_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_demo_updated_time ON public.gen_demo USING btree (updated_time);


--
-- Name: ix_gen_demo_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_gen_demo_uuid ON public.gen_demo USING btree (uuid);


--
-- Name: ix_gen_table_column_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_created_id ON public.gen_table_column USING btree (created_id);


--
-- Name: ix_gen_table_column_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_created_time ON public.gen_table_column USING btree (created_time);


--
-- Name: ix_gen_table_column_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_id ON public.gen_table_column USING btree (id);


--
-- Name: ix_gen_table_column_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_status ON public.gen_table_column USING btree (status);


--
-- Name: ix_gen_table_column_table_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_table_id ON public.gen_table_column USING btree (table_id);


--
-- Name: ix_gen_table_column_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_updated_id ON public.gen_table_column USING btree (updated_id);


--
-- Name: ix_gen_table_column_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_column_updated_time ON public.gen_table_column USING btree (updated_time);


--
-- Name: ix_gen_table_column_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_gen_table_column_uuid ON public.gen_table_column USING btree (uuid);


--
-- Name: ix_gen_table_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_created_id ON public.gen_table USING btree (created_id);


--
-- Name: ix_gen_table_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_created_time ON public.gen_table USING btree (created_time);


--
-- Name: ix_gen_table_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_id ON public.gen_table USING btree (id);


--
-- Name: ix_gen_table_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_status ON public.gen_table USING btree (status);


--
-- Name: ix_gen_table_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_updated_id ON public.gen_table USING btree (updated_id);


--
-- Name: ix_gen_table_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_gen_table_updated_time ON public.gen_table USING btree (updated_time);


--
-- Name: ix_gen_table_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_gen_table_uuid ON public.gen_table USING btree (uuid);


--
-- Name: ix_sys_dept_code; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_code ON public.sys_dept USING btree (code);


--
-- Name: ix_sys_dept_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_created_time ON public.sys_dept USING btree (created_time);


--
-- Name: ix_sys_dept_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_id ON public.sys_dept USING btree (id);


--
-- Name: ix_sys_dept_parent_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_parent_id ON public.sys_dept USING btree (parent_id);


--
-- Name: ix_sys_dept_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_status ON public.sys_dept USING btree (status);


--
-- Name: ix_sys_dept_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dept_updated_time ON public.sys_dept USING btree (updated_time);


--
-- Name: ix_sys_dept_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_dept_uuid ON public.sys_dept USING btree (uuid);


--
-- Name: ix_sys_dict_data_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_data_created_time ON public.sys_dict_data USING btree (created_time);


--
-- Name: ix_sys_dict_data_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_data_id ON public.sys_dict_data USING btree (id);


--
-- Name: ix_sys_dict_data_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_data_status ON public.sys_dict_data USING btree (status);


--
-- Name: ix_sys_dict_data_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_data_updated_time ON public.sys_dict_data USING btree (updated_time);


--
-- Name: ix_sys_dict_data_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_dict_data_uuid ON public.sys_dict_data USING btree (uuid);


--
-- Name: ix_sys_dict_type_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_type_created_time ON public.sys_dict_type USING btree (created_time);


--
-- Name: ix_sys_dict_type_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_type_id ON public.sys_dict_type USING btree (id);


--
-- Name: ix_sys_dict_type_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_type_status ON public.sys_dict_type USING btree (status);


--
-- Name: ix_sys_dict_type_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_dict_type_updated_time ON public.sys_dict_type USING btree (updated_time);


--
-- Name: ix_sys_dict_type_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_dict_type_uuid ON public.sys_dict_type USING btree (uuid);


--
-- Name: ix_sys_log_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_created_id ON public.sys_log USING btree (created_id);


--
-- Name: ix_sys_log_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_created_time ON public.sys_log USING btree (created_time);


--
-- Name: ix_sys_log_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_id ON public.sys_log USING btree (id);


--
-- Name: ix_sys_log_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_status ON public.sys_log USING btree (status);


--
-- Name: ix_sys_log_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_updated_id ON public.sys_log USING btree (updated_id);


--
-- Name: ix_sys_log_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_log_updated_time ON public.sys_log USING btree (updated_time);


--
-- Name: ix_sys_log_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_log_uuid ON public.sys_log USING btree (uuid);


--
-- Name: ix_sys_menu_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_menu_created_time ON public.sys_menu USING btree (created_time);


--
-- Name: ix_sys_menu_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_menu_id ON public.sys_menu USING btree (id);


--
-- Name: ix_sys_menu_parent_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_menu_parent_id ON public.sys_menu USING btree (parent_id);


--
-- Name: ix_sys_menu_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_menu_status ON public.sys_menu USING btree (status);


--
-- Name: ix_sys_menu_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_menu_updated_time ON public.sys_menu USING btree (updated_time);


--
-- Name: ix_sys_menu_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_menu_uuid ON public.sys_menu USING btree (uuid);


--
-- Name: ix_sys_notice_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_created_id ON public.sys_notice USING btree (created_id);


--
-- Name: ix_sys_notice_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_created_time ON public.sys_notice USING btree (created_time);


--
-- Name: ix_sys_notice_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_id ON public.sys_notice USING btree (id);


--
-- Name: ix_sys_notice_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_status ON public.sys_notice USING btree (status);


--
-- Name: ix_sys_notice_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_updated_id ON public.sys_notice USING btree (updated_id);


--
-- Name: ix_sys_notice_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_notice_updated_time ON public.sys_notice USING btree (updated_time);


--
-- Name: ix_sys_notice_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_notice_uuid ON public.sys_notice USING btree (uuid);


--
-- Name: ix_sys_param_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_param_created_time ON public.sys_param USING btree (created_time);


--
-- Name: ix_sys_param_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_param_id ON public.sys_param USING btree (id);


--
-- Name: ix_sys_param_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_param_status ON public.sys_param USING btree (status);


--
-- Name: ix_sys_param_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_param_updated_time ON public.sys_param USING btree (updated_time);


--
-- Name: ix_sys_param_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_param_uuid ON public.sys_param USING btree (uuid);


--
-- Name: ix_sys_position_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_created_id ON public.sys_position USING btree (created_id);


--
-- Name: ix_sys_position_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_created_time ON public.sys_position USING btree (created_time);


--
-- Name: ix_sys_position_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_id ON public.sys_position USING btree (id);


--
-- Name: ix_sys_position_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_status ON public.sys_position USING btree (status);


--
-- Name: ix_sys_position_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_updated_id ON public.sys_position USING btree (updated_id);


--
-- Name: ix_sys_position_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_position_updated_time ON public.sys_position USING btree (updated_time);


--
-- Name: ix_sys_position_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_position_uuid ON public.sys_position USING btree (uuid);


--
-- Name: ix_sys_role_code; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_role_code ON public.sys_role USING btree (code);


--
-- Name: ix_sys_role_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_role_created_time ON public.sys_role USING btree (created_time);


--
-- Name: ix_sys_role_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_role_id ON public.sys_role USING btree (id);


--
-- Name: ix_sys_role_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_role_status ON public.sys_role USING btree (status);


--
-- Name: ix_sys_role_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_role_updated_time ON public.sys_role USING btree (updated_time);


--
-- Name: ix_sys_role_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_role_uuid ON public.sys_role USING btree (uuid);


--
-- Name: ix_sys_user_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_created_id ON public.sys_user USING btree (created_id);


--
-- Name: ix_sys_user_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_created_time ON public.sys_user USING btree (created_time);


--
-- Name: ix_sys_user_dept_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_dept_id ON public.sys_user USING btree (dept_id);


--
-- Name: ix_sys_user_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_id ON public.sys_user USING btree (id);


--
-- Name: ix_sys_user_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_status ON public.sys_user USING btree (status);


--
-- Name: ix_sys_user_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_updated_id ON public.sys_user USING btree (updated_id);


--
-- Name: ix_sys_user_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_sys_user_updated_time ON public.sys_user USING btree (updated_time);


--
-- Name: ix_sys_user_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_sys_user_uuid ON public.sys_user USING btree (uuid);


--
-- Name: ix_task_job_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_job_created_time ON public.task_job USING btree (created_time);


--
-- Name: ix_task_job_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_job_id ON public.task_job USING btree (id);


--
-- Name: ix_task_job_job_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_job_job_id ON public.task_job USING btree (job_id);


--
-- Name: ix_task_job_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_job_updated_time ON public.task_job USING btree (updated_time);


--
-- Name: ix_task_job_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_task_job_uuid ON public.task_job USING btree (uuid);


--
-- Name: ix_task_node_created_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_created_id ON public.task_node USING btree (created_id);


--
-- Name: ix_task_node_created_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_created_time ON public.task_node USING btree (created_time);


--
-- Name: ix_task_node_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_id ON public.task_node USING btree (id);


--
-- Name: ix_task_node_status; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_status ON public.task_node USING btree (status);


--
-- Name: ix_task_node_updated_id; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_updated_id ON public.task_node USING btree (updated_id);


--
-- Name: ix_task_node_updated_time; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ix_task_node_updated_time ON public.task_node USING btree (updated_time);


--
-- Name: ix_task_node_uuid; Type: INDEX; Schema: public; Owner: root
--

CREATE UNIQUE INDEX ix_task_node_uuid ON public.task_node USING btree (uuid);


--
-- Name: app_myapp app_myapp_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.app_myapp
    ADD CONSTRAINT app_myapp_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: app_myapp app_myapp_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.app_myapp
    ADD CONSTRAINT app_myapp_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_demo gen_demo_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_demo
    ADD CONSTRAINT gen_demo_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_demo gen_demo_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_demo
    ADD CONSTRAINT gen_demo_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_table_column gen_table_column_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table_column
    ADD CONSTRAINT gen_table_column_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_table_column gen_table_column_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table_column
    ADD CONSTRAINT gen_table_column_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.gen_table(id) ON DELETE CASCADE;


--
-- Name: gen_table_column gen_table_column_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table_column
    ADD CONSTRAINT gen_table_column_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_table gen_table_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table
    ADD CONSTRAINT gen_table_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: gen_table gen_table_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.gen_table
    ADD CONSTRAINT gen_table_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_dept sys_dept_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dept
    ADD CONSTRAINT sys_dept_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.sys_dept(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_dict_data sys_dict_data_dict_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_dict_data
    ADD CONSTRAINT sys_dict_data_dict_type_id_fkey FOREIGN KEY (dict_type_id) REFERENCES public.sys_dict_type(id) ON DELETE CASCADE;


--
-- Name: sys_log sys_log_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_log
    ADD CONSTRAINT sys_log_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_log sys_log_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_log
    ADD CONSTRAINT sys_log_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_menu sys_menu_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_menu
    ADD CONSTRAINT sys_menu_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.sys_menu(id) ON DELETE SET NULL;


--
-- Name: sys_notice sys_notice_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_notice
    ADD CONSTRAINT sys_notice_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_notice sys_notice_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_notice
    ADD CONSTRAINT sys_notice_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_position sys_position_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_position
    ADD CONSTRAINT sys_position_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_position sys_position_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_position
    ADD CONSTRAINT sys_position_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_role_depts sys_role_depts_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_depts
    ADD CONSTRAINT sys_role_depts_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES public.sys_dept(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_role_depts sys_role_depts_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_depts
    ADD CONSTRAINT sys_role_depts_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.sys_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_role_menus sys_role_menus_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_menus
    ADD CONSTRAINT sys_role_menus_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.sys_menu(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_role_menus sys_role_menus_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_role_menus
    ADD CONSTRAINT sys_role_menus_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.sys_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_user sys_user_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_user sys_user_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_dept_id_fkey FOREIGN KEY (dept_id) REFERENCES public.sys_dept(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sys_user_positions sys_user_positions_position_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_positions
    ADD CONSTRAINT sys_user_positions_position_id_fkey FOREIGN KEY (position_id) REFERENCES public.sys_position(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_user_positions sys_user_positions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_positions
    ADD CONSTRAINT sys_user_positions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_user_roles sys_user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_roles
    ADD CONSTRAINT sys_user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.sys_role(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_user_roles sys_user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user_roles
    ADD CONSTRAINT sys_user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sys_user sys_user_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: task_node task_node_created_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_node
    ADD CONSTRAINT task_node_created_id_fkey FOREIGN KEY (created_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: task_node task_node_updated_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.task_node
    ADD CONSTRAINT task_node_updated_id_fkey FOREIGN KEY (updated_id) REFERENCES public.sys_user(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict XtHgo6tsQhuEdNKh15hA2RTTBSfxiXqx9DJbJFNHFfxtyyZ8jR5tz7beQUpdNxG


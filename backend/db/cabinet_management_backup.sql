--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1)

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
-- Name: public; Type: SCHEMA; Schema: -; Owner: cabinet_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO cabinet_user;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: cabinet_user
--

COMMENT ON SCHEMA public IS '';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: allergy_severity; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.allergy_severity AS ENUM (
    'mild',
    'moderate',
    'severe',
    'life_threatening'
);


ALTER TYPE public.allergy_severity OWNER TO cabinet_user;

--
-- Name: allergy_type; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.allergy_type AS ENUM (
    'food',
    'drug',
    'environmental',
    'other'
);


ALTER TYPE public.allergy_type OWNER TO cabinet_user;

--
-- Name: appointment_status; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.appointment_status AS ENUM (
    'scheduled',
    'confirmed',
    'completed',
    'cancelled',
    'no_show'
);


ALTER TYPE public.appointment_status OWNER TO cabinet_user;

--
-- Name: blood_type; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.blood_type AS ENUM (
    'A+',
    'A-',
    'B+',
    'B-',
    'AB+',
    'AB-',
    'O+',
    'O-'
);


ALTER TYPE public.blood_type OWNER TO cabinet_user;

--
-- Name: diagnosis_certainty; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.diagnosis_certainty AS ENUM (
    'confirmed',
    'probable',
    'suspected',
    'ruled_out'
);


ALTER TYPE public.diagnosis_certainty OWNER TO cabinet_user;

--
-- Name: gender_type; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.gender_type AS ENUM (
    'male',
    'female',
    'other'
);


ALTER TYPE public.gender_type OWNER TO cabinet_user;

--
-- Name: marital_status; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.marital_status AS ENUM (
    'single',
    'married',
    'divorced',
    'widowed'
);


ALTER TYPE public.marital_status OWNER TO cabinet_user;

--
-- Name: payment_method; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.payment_method AS ENUM (
    'cash',
    'check',
    'card',
    'transfer'
);


ALTER TYPE public.payment_method OWNER TO cabinet_user;

--
-- Name: staff_gender; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.staff_gender AS ENUM (
    'M',
    'F',
    'O'
);


ALTER TYPE public.staff_gender OWNER TO cabinet_user;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'doctor',
    'staff'
);


ALTER TYPE public.user_role OWNER TO cabinet_user;

--
-- Name: visit_type; Type: TYPE; Schema: public; Owner: cabinet_user
--

CREATE TYPE public.visit_type AS ENUM (
    'consultation',
    'follow_up',
    'emergency',
    'routine_checkup'
);


ALTER TYPE public.visit_type OWNER TO cabinet_user;

--
-- Name: check_permission(integer, character varying, character varying); Type: FUNCTION; Schema: public; Owner: cabinet_user
--

CREATE FUNCTION public.check_permission(p_user_id integer, p_module_name character varying, p_action character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_has_permission BOOLEAN;
    v_user_role_id INTEGER;
BEGIN
    -- Get user's role
    SELECT role_id INTO v_user_role_id 
    FROM system_users 
    WHERE id = p_user_id AND deleted_at IS NULL AND is_active = TRUE;
    
    IF v_user_role_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user is super admin (has all permissions)
    IF EXISTS (SELECT 1 FROM roles WHERE id = v_user_role_id AND name = 'superadmin') THEN
        RETURN TRUE;
    END IF;
    
    -- Check specific permission
    SELECT 
        CASE p_action
            WHEN 'create' THEN can_create
            WHEN 'read' THEN can_read
            WHEN 'update' THEN can_update
            WHEN 'delete' THEN can_delete
            WHEN 'export' THEN can_export
            WHEN 'manage_users' THEN can_manage_users
            ELSE FALSE
        END INTO v_has_permission
    FROM role_permissions rp
    JOIN modules m ON rp.module_id = m.id
    WHERE rp.role_id = v_user_role_id AND m.name = p_module_name;
    
    RETURN COALESCE(v_has_permission, FALSE);
END;
$$;


ALTER FUNCTION public.check_permission(p_user_id integer, p_module_name character varying, p_action character varying) OWNER TO cabinet_user;

--
-- Name: FUNCTION check_permission(p_user_id integer, p_module_name character varying, p_action character varying); Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON FUNCTION public.check_permission(p_user_id integer, p_module_name character varying, p_action character varying) IS 'Checks if a user has specific permission for a module action';


--
-- Name: log_audit_event(); Type: FUNCTION; Schema: public; Owner: cabinet_user
--

CREATE FUNCTION public.log_audit_event() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_action TEXT;
    v_user_id INTEGER;
BEGIN
    v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
    
    IF TG_OP = 'INSERT' THEN
        v_action := 'INSERT';
        v_new_data := to_jsonb(NEW);
        v_old_data := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE';
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    END IF;

    INSERT INTO audit_logs (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        user_id,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        v_action,
        v_old_data,
        v_new_data,
        v_user_id,
        current_setting('app.ip_address', TRUE)::INET,
        current_setting('app.user_agent', TRUE)
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.log_audit_event() OWNER TO cabinet_user;

--
-- Name: set_audit_fields(); Type: FUNCTION; Schema: public; Owner: cabinet_user
--

CREATE FUNCTION public.set_audit_fields() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.created_by = COALESCE(NEW.created_by, current_setting('app.current_user_id', TRUE)::INTEGER);
        NEW.updated_by = NEW.created_by;
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.updated_by = COALESCE(NEW.updated_by, current_setting('app.current_user_id', TRUE)::INTEGER);
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_audit_fields() OWNER TO cabinet_user;

--
-- Name: soft_delete_record(); Type: FUNCTION; Schema: public; Owner: cabinet_user
--

CREATE FUNCTION public.soft_delete_record() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.deleted_at = CURRENT_TIMESTAMP;
    NEW.deleted_by = current_setting('app.current_user_id', TRUE)::INTEGER;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.soft_delete_record() OWNER TO cabinet_user;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: cabinet_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO cabinet_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: appointments; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.appointments (
    id integer NOT NULL,
    appointment_code character varying(20) NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    appointment_date date NOT NULL,
    appointment_time time without time zone NOT NULL,
    appointment_type character varying(50),
    status public.appointment_status DEFAULT 'scheduled'::public.appointment_status,
    reason_for_visit text,
    notes text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.appointments OWNER TO cabinet_user;

--
-- Name: system_users; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.system_users (
    id integer NOT NULL,
    staff_id integer NOT NULL,
    username character varying(150) NOT NULL,
    password_hash text NOT NULL,
    role_id integer NOT NULL,
    is_active boolean DEFAULT true,
    last_login timestamp with time zone,
    must_change_password boolean DEFAULT false,
    login_attempts integer DEFAULT 0,
    locked_until timestamp with time zone,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.system_users OWNER TO cabinet_user;

--
-- Name: TABLE system_users; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON TABLE public.system_users IS '
Application Usage:
1. Set user context before operations:
   SELECT set_config(''app.current_user_id'', ''1'', false);
   SELECT set_config(''app.ip_address'', ''192.168.1.1'', false);
   SELECT set_config(''app.user_agent'', ''Mozilla/5.0...'', false);

2. Check permissions:
   SELECT check_permission(1, ''patients'', ''create'');

3. Insert records (audit fields auto-populated):
   INSERT INTO patients (patient_code, first_name, last_name) VALUES (''PAT004'', ''John'', ''Doe'');

4. View user permissions:
   SELECT * FROM user_permissions WHERE user_id = 1;
';


--
-- Name: active_appointments; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_appointments AS
 SELECT a.id,
    a.appointment_code,
    a.patient_id,
    a.doctor_id,
    a.appointment_date,
    a.appointment_time,
    a.appointment_type,
    a.status,
    a.reason_for_visit,
    a.notes,
    a.created_by,
    a.updated_by,
    a.created_at,
    a.updated_at,
    a.deleted_at,
    a.deleted_by,
    u1.username AS created_by_username,
    u2.username AS updated_by_username
   FROM ((public.appointments a
     LEFT JOIN public.system_users u1 ON ((a.created_by = u1.id)))
     LEFT JOIN public.system_users u2 ON ((a.updated_by = u2.id)))
  WHERE (a.deleted_at IS NULL);


ALTER VIEW public.active_appointments OWNER TO postgres;

--
-- Name: doctors; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.doctors (
    id integer NOT NULL,
    doctor_code character varying(20) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    specialization character varying(100),
    license_number character varying(100),
    email character varying(255),
    phone character varying(20),
    mobile character varying(20),
    address text,
    city character varying(100),
    is_active boolean DEFAULT true,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.doctors OWNER TO cabinet_user;

--
-- Name: COLUMN doctors.created_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.doctors.created_by IS 'User who created this doctor record';


--
-- Name: COLUMN doctors.updated_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.doctors.updated_by IS 'User who last updated this doctor record';


--
-- Name: COLUMN doctors.deleted_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.doctors.deleted_by IS 'User who soft deleted this doctor record';


--
-- Name: active_doctors; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_doctors AS
 SELECT d.id,
    d.doctor_code,
    d.first_name,
    d.last_name,
    d.specialization,
    d.license_number,
    d.email,
    d.phone,
    d.mobile,
    d.address,
    d.city,
    d.is_active,
    d.created_by,
    d.updated_by,
    d.created_at,
    d.updated_at,
    d.deleted_at,
    d.deleted_by,
    u1.username AS created_by_username,
    u2.username AS updated_by_username
   FROM ((public.doctors d
     LEFT JOIN public.system_users u1 ON ((d.created_by = u1.id)))
     LEFT JOIN public.system_users u2 ON ((d.updated_by = u2.id)))
  WHERE (d.deleted_at IS NULL);


ALTER VIEW public.active_doctors OWNER TO postgres;

--
-- Name: patient_visits; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.patient_visits (
    id integer NOT NULL,
    visit_code character varying(20) NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    visit_date date NOT NULL,
    visit_time time without time zone,
    visit_type public.visit_type,
    chief_complaint text,
    diagnosis text,
    clinical_notes text,
    weight numeric(5,2),
    height numeric(5,2),
    blood_pressure_systolic integer,
    blood_pressure_diastolic integer,
    blood_glucose numeric(5,2),
    temperature numeric(4,2),
    status character varying(50) DEFAULT 'completed'::character varying,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.patient_visits OWNER TO cabinet_user;

--
-- Name: active_patient_visits; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_patient_visits AS
 SELECT pv.id,
    pv.visit_code,
    pv.patient_id,
    pv.doctor_id,
    pv.visit_date,
    pv.visit_time,
    pv.visit_type,
    pv.chief_complaint,
    pv.diagnosis,
    pv.clinical_notes,
    pv.weight,
    pv.height,
    pv.blood_pressure_systolic,
    pv.blood_pressure_diastolic,
    pv.blood_glucose,
    pv.temperature,
    pv.status,
    pv.created_by,
    pv.updated_by,
    pv.created_at,
    pv.updated_at,
    pv.deleted_at,
    pv.deleted_by,
    u1.username AS created_by_username,
    u2.username AS updated_by_username
   FROM ((public.patient_visits pv
     LEFT JOIN public.system_users u1 ON ((pv.created_by = u1.id)))
     LEFT JOIN public.system_users u2 ON ((pv.updated_by = u2.id)))
  WHERE (pv.deleted_at IS NULL);


ALTER VIEW public.active_patient_visits OWNER TO postgres;

--
-- Name: patients; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    patient_code character varying(20) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    date_of_birth date,
    gender public.gender_type,
    marital_status public.marital_status,
    blood_type public.blood_type,
    place_of_birth character varying(255),
    medical_history text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.patients OWNER TO cabinet_user;

--
-- Name: COLUMN patients.created_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.patients.created_by IS 'User who created this patient record';


--
-- Name: COLUMN patients.updated_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.patients.updated_by IS 'User who last updated this patient record';


--
-- Name: COLUMN patients.deleted_by; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON COLUMN public.patients.deleted_by IS 'User who soft deleted this patient record';


--
-- Name: active_patients; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_patients AS
 SELECT p.id,
    p.patient_code,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.gender,
    p.marital_status,
    p.blood_type,
    p.place_of_birth,
    p.medical_history,
    p.created_by,
    p.updated_by,
    p.created_at,
    p.updated_at,
    p.deleted_at,
    p.deleted_by,
    u1.username AS created_by_username,
    u2.username AS updated_by_username
   FROM ((public.patients p
     LEFT JOIN public.system_users u1 ON ((p.created_by = u1.id)))
     LEFT JOIN public.system_users u2 ON ((p.updated_by = u2.id)))
  WHERE (p.deleted_at IS NULL);


ALTER VIEW public.active_patients OWNER TO postgres;

--
-- Name: staff; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.staff (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    date_of_birth date,
    gender public.staff_gender,
    marital_status character varying(50),
    mobile_phone character varying(20),
    home_phone character varying(20),
    fax character varying(20),
    email character varying(150),
    country character varying(100),
    region character varying(100),
    city character varying(100),
    profile_image text,
    "position" character varying(100),
    hire_date date,
    department character varying(100),
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer,
    department_id integer,
    role_id integer,
    doctor_code character varying(20),
    specialization character varying(100),
    license_number character varying(100)
);


ALTER TABLE public.staff OWNER TO cabinet_user;

--
-- Name: TABLE staff; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON TABLE public.staff IS 'All staff members working in the clinic';


--
-- Name: active_staff; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.active_staff AS
 SELECT s.id,
    s.first_name,
    s.last_name,
    s.date_of_birth,
    s.gender,
    s.marital_status,
    s.mobile_phone,
    s.home_phone,
    s.fax,
    s.email,
    s.country,
    s.region,
    s.city,
    s.profile_image,
    s."position",
    s.hire_date,
    s.department,
    s.created_by,
    s.updated_by,
    s.created_at,
    s.updated_at,
    s.deleted_at,
    s.deleted_by,
    u1.username AS created_by_username,
    u2.username AS updated_by_username
   FROM ((public.staff s
     LEFT JOIN public.system_users u1 ON ((s.created_by = u1.id)))
     LEFT JOIN public.system_users u2 ON ((s.updated_by = u2.id)))
  WHERE (s.deleted_at IS NULL);


ALTER VIEW public.active_staff OWNER TO postgres;

--
-- Name: allergies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.allergies (
    id integer NOT NULL,
    allergy_name character varying(255) NOT NULL,
    allergy_type public.allergy_type NOT NULL,
    description text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.allergies OWNER TO postgres;

--
-- Name: allergies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.allergies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.allergies_id_seq OWNER TO postgres;

--
-- Name: allergies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.allergies_id_seq OWNED BY public.allergies.id;


--
-- Name: appointment_slots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.appointment_slots (
    id integer NOT NULL,
    slot_index integer NOT NULL,
    slot_time time without time zone NOT NULL,
    is_available boolean DEFAULT true,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.appointment_slots OWNER TO postgres;

--
-- Name: appointment_slots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.appointment_slots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.appointment_slots_id_seq OWNER TO postgres;

--
-- Name: appointment_slots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.appointment_slots_id_seq OWNED BY public.appointment_slots.id;


--
-- Name: appointments_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.appointments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.appointments_id_seq OWNER TO cabinet_user;

--
-- Name: appointments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.appointments_id_seq OWNED BY public.appointments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    table_name character varying(100) NOT NULL,
    record_id integer NOT NULL,
    action character varying(20) NOT NULL,
    old_values jsonb,
    new_values jsonb,
    user_id integer,
    ip_address inet,
    user_agent text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.audit_logs OWNER TO cabinet_user;

--
-- Name: TABLE audit_logs; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON TABLE public.audit_logs IS 'Comprehensive audit trail for all data changes';


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO cabinet_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: banks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.banks (
    id integer NOT NULL,
    bank_code character varying(20) NOT NULL,
    bank_name character varying(255) NOT NULL,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.banks OWNER TO postgres;

--
-- Name: banks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.banks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.banks_id_seq OWNER TO postgres;

--
-- Name: banks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.banks_id_seq OWNED BY public.banks.id;


--
-- Name: billing_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.billing_categories (
    id integer NOT NULL,
    category_code character varying(20) NOT NULL,
    category_name character varying(255) NOT NULL,
    description text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.billing_categories OWNER TO postgres;

--
-- Name: billing_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.billing_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.billing_categories_id_seq OWNER TO postgres;

--
-- Name: billing_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.billing_categories_id_seq OWNED BY public.billing_categories.id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.departments (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    head_id integer,
    created_by integer,
    updated_by integer,
    deleted_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone
);


ALTER TABLE public.departments OWNER TO postgres;

--
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.departments_id_seq OWNER TO postgres;

--
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- Name: doctor_specialties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.doctor_specialties (
    id integer NOT NULL,
    doctor_id integer NOT NULL,
    specialty character varying(100) NOT NULL,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.doctor_specialties OWNER TO postgres;

--
-- Name: doctor_specialties_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.doctor_specialties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctor_specialties_id_seq OWNER TO postgres;

--
-- Name: doctor_specialties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.doctor_specialties_id_seq OWNED BY public.doctor_specialties.id;


--
-- Name: doctors_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.doctors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctors_id_seq OWNER TO cabinet_user;

--
-- Name: doctors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.doctors_id_seq OWNED BY public.doctors.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    expense_code character varying(20) NOT NULL,
    expense_date date NOT NULL,
    amount numeric(10,2) NOT NULL,
    category_id integer,
    description text,
    payment_method public.payment_method,
    bank_name character varying(100),
    check_number character varying(50),
    recorded_by_doctor_id integer,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.expenses OWNER TO postgres;

--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expenses_id_seq OWNER TO postgres;

--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: lab_orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lab_orders (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    test_id integer NOT NULL,
    ordering_doctor_id integer NOT NULL,
    order_date date NOT NULL,
    laboratory_name character varying(255),
    clinical_notes text,
    results text,
    result_date date,
    is_abnormal boolean,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.lab_orders OWNER TO postgres;

--
-- Name: lab_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lab_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lab_orders_id_seq OWNER TO postgres;

--
-- Name: lab_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lab_orders_id_seq OWNED BY public.lab_orders.id;


--
-- Name: lab_tests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lab_tests (
    id integer NOT NULL,
    test_code character varying(20) NOT NULL,
    test_name character varying(255) NOT NULL,
    category character varying(100),
    description text,
    specimen_type character varying(100),
    reference_range_min numeric(10,2),
    reference_range_max numeric(10,2),
    measurement_unit character varying(50),
    is_favorite boolean DEFAULT false,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.lab_tests OWNER TO postgres;

--
-- Name: lab_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lab_tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lab_tests_id_seq OWNER TO postgres;

--
-- Name: lab_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lab_tests_id_seq OWNED BY public.lab_tests.id;


--
-- Name: medical_certificates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_certificates (
    id integer NOT NULL,
    certificate_code character varying(20) NOT NULL,
    patient_id integer NOT NULL,
    issuing_doctor_id integer NOT NULL,
    issue_date date NOT NULL,
    certificate_type character varying(100) NOT NULL,
    work_resumption_date date,
    accident_date date,
    medical_findings text,
    restrictions text,
    duration_days integer,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.medical_certificates OWNER TO postgres;

--
-- Name: medical_certificates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medical_certificates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_certificates_id_seq OWNER TO postgres;

--
-- Name: medical_certificates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medical_certificates_id_seq OWNED BY public.medical_certificates.id;


--
-- Name: medical_conditions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_conditions (
    id integer NOT NULL,
    condition_code character varying(20) NOT NULL,
    condition_name character varying(255) NOT NULL,
    category character varying(100),
    icd_code character varying(20),
    description text,
    general_information text,
    diagnostic_criteria text,
    treatment_guidelines text,
    is_favorite boolean DEFAULT false,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.medical_conditions OWNER TO postgres;

--
-- Name: medical_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medical_conditions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_conditions_id_seq OWNER TO postgres;

--
-- Name: medical_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medical_conditions_id_seq OWNED BY public.medical_conditions.id;


--
-- Name: medical_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_reports (
    id integer NOT NULL,
    report_code character varying(20) NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    report_date date NOT NULL,
    report_type character varying(100),
    title character varying(255),
    content text,
    additional_notes text,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.medical_reports OWNER TO postgres;

--
-- Name: medical_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medical_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_reports_id_seq OWNER TO postgres;

--
-- Name: medical_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medical_reports_id_seq OWNED BY public.medical_reports.id;


--
-- Name: medical_services; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.medical_services (
    id integer NOT NULL,
    service_code character varying(20) NOT NULL,
    service_name character varying(255) NOT NULL,
    description text,
    standard_price numeric(10,2) NOT NULL,
    is_active boolean DEFAULT true,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.medical_services OWNER TO cabinet_user;

--
-- Name: medical_services_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.medical_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_services_id_seq OWNER TO cabinet_user;

--
-- Name: medical_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.medical_services_id_seq OWNED BY public.medical_services.id;


--
-- Name: medications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medications (
    id integer NOT NULL,
    medication_code character varying(20) NOT NULL,
    generic_name character varying(255) NOT NULL,
    brand_name character varying(255),
    pharmaceutical_form character varying(100),
    dosage_strength character varying(100),
    manufacturer character varying(255),
    unit_price numeric(10,2),
    is_active boolean DEFAULT true,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.medications OWNER TO postgres;

--
-- Name: medications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medications_id_seq OWNER TO postgres;

--
-- Name: medications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medications_id_seq OWNED BY public.medications.id;


--
-- Name: modules; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.modules (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.modules OWNER TO cabinet_user;

--
-- Name: modules_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.modules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.modules_id_seq OWNER TO cabinet_user;

--
-- Name: modules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.modules_id_seq OWNED BY public.modules.id;


--
-- Name: patient_allergies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_allergies (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    allergy_id integer NOT NULL,
    severity public.allergy_severity,
    reaction_description text,
    diagnosed_date date,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.patient_allergies OWNER TO postgres;

--
-- Name: patient_allergies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_allergies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_allergies_id_seq OWNER TO postgres;

--
-- Name: patient_allergies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_allergies_id_seq OWNED BY public.patient_allergies.id;


--
-- Name: patient_diagnoses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_diagnoses (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    condition_id integer NOT NULL,
    diagnosis_date date NOT NULL,
    diagnosing_doctor_id integer NOT NULL,
    certainty_level public.diagnosis_certainty,
    notes text,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.patient_diagnoses OWNER TO postgres;

--
-- Name: patient_diagnoses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_diagnoses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_diagnoses_id_seq OWNER TO postgres;

--
-- Name: patient_diagnoses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_diagnoses_id_seq OWNED BY public.patient_diagnoses.id;


--
-- Name: patient_payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_payments (
    id integer NOT NULL,
    payment_code character varying(20) NOT NULL,
    visit_id integer NOT NULL,
    payment_date date NOT NULL,
    amount numeric(10,2) NOT NULL,
    payment_method public.payment_method NOT NULL,
    bank_name character varying(100),
    check_number character varying(50),
    notes text,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.patient_payments OWNER TO postgres;

--
-- Name: patient_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_payments_id_seq OWNER TO postgres;

--
-- Name: patient_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_payments_id_seq OWNED BY public.patient_payments.id;


--
-- Name: patient_visits_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.patient_visits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_visits_id_seq OWNER TO cabinet_user;

--
-- Name: patient_visits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.patient_visits_id_seq OWNED BY public.patient_visits.id;


--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_id_seq OWNER TO cabinet_user;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: pharmacies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pharmacies (
    id integer NOT NULL,
    pharmacy_code character varying(20) NOT NULL,
    pharmacy_name character varying(255) NOT NULL,
    owner_name character varying(100),
    address text,
    city character varying(100),
    phone character varying(20),
    mobile character varying(20),
    email character varying(100),
    is_active boolean DEFAULT true,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.pharmacies OWNER TO postgres;

--
-- Name: pharmacies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pharmacies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pharmacies_id_seq OWNER TO postgres;

--
-- Name: pharmacies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pharmacies_id_seq OWNED BY public.pharmacies.id;


--
-- Name: prescriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prescriptions (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    medication_id integer NOT NULL,
    prescribing_doctor_id integer NOT NULL,
    dosage_instructions text NOT NULL,
    quantity_prescribed integer,
    duration_days integer,
    is_free boolean DEFAULT false,
    refills_allowed integer DEFAULT 0,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.prescriptions OWNER TO postgres;

--
-- Name: prescriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.prescriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prescriptions_id_seq OWNER TO postgres;

--
-- Name: prescriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.prescriptions_id_seq OWNED BY public.prescriptions.id;


--
-- Name: radiology_exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.radiology_exams (
    id integer NOT NULL,
    exam_code character varying(20) NOT NULL,
    exam_name character varying(255) NOT NULL,
    category character varying(100),
    exam_type character varying(50),
    is_favorite boolean DEFAULT false,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.radiology_exams OWNER TO postgres;

--
-- Name: radiology_exams_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.radiology_exams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.radiology_exams_id_seq OWNER TO postgres;

--
-- Name: radiology_exams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.radiology_exams_id_seq OWNED BY public.radiology_exams.id;


--
-- Name: radiology_orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.radiology_orders (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    exam_id integer NOT NULL,
    ordering_doctor_id integer NOT NULL,
    order_date date NOT NULL,
    imaging_center character varying(255),
    clinical_notes text,
    radiology_report text,
    findings text,
    conclusion text,
    report_date date,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.radiology_orders OWNER TO postgres;

--
-- Name: radiology_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.radiology_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.radiology_orders_id_seq OWNER TO postgres;

--
-- Name: radiology_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.radiology_orders_id_seq OWNED BY public.radiology_orders.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role_id integer NOT NULL,
    module_id integer NOT NULL,
    can_create boolean DEFAULT false,
    can_read boolean DEFAULT false,
    can_update boolean DEFAULT false,
    can_delete boolean DEFAULT false,
    can_export boolean DEFAULT false,
    can_manage_users boolean DEFAULT false,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.role_permissions OWNER TO cabinet_user;

--
-- Name: TABLE role_permissions; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON TABLE public.role_permissions IS 'Detailed permissions for each role per module';


--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_permissions_id_seq OWNER TO cabinet_user;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description text,
    created_by integer,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.roles OWNER TO cabinet_user;

--
-- Name: TABLE roles; Type: COMMENT; Schema: public; Owner: cabinet_user
--

COMMENT ON TABLE public.roles IS 'System roles with different permission levels';


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO cabinet_user;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: staff_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.staff_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.staff_id_seq OWNER TO cabinet_user;

--
-- Name: staff_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.staff_id_seq OWNED BY public.staff.id;


--
-- Name: symptoms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.symptoms (
    id integer NOT NULL,
    symptom_code character varying(20) NOT NULL,
    symptom_name character varying(255) NOT NULL,
    description text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.symptoms OWNER TO postgres;

--
-- Name: symptoms_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.symptoms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.symptoms_id_seq OWNER TO postgres;

--
-- Name: symptoms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.symptoms_id_seq OWNED BY public.symptoms.id;


--
-- Name: system_users_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.system_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_users_id_seq OWNER TO cabinet_user;

--
-- Name: system_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.system_users_id_seq OWNED BY public.system_users.id;


--
-- Name: user_permissions; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.user_permissions AS
 SELECT su.id AS user_id,
    su.username,
    s.first_name,
    s.last_name,
    r.name AS role_name,
    m.name AS module_name,
    rp.can_create,
    rp.can_read,
    rp.can_update,
    rp.can_delete,
    rp.can_export,
    rp.can_manage_users
   FROM ((((public.system_users su
     JOIN public.staff s ON ((su.staff_id = s.id)))
     JOIN public.roles r ON ((su.role_id = r.id)))
     JOIN public.role_permissions rp ON ((r.id = rp.role_id)))
     JOIN public.modules m ON ((rp.module_id = m.id)))
  WHERE ((su.deleted_at IS NULL) AND (su.is_active = true) AND (r.deleted_at IS NULL));


ALTER VIEW public.user_permissions OWNER TO postgres;

--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: cabinet_user
--

CREATE TABLE public.user_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    session_token character varying(255) NOT NULL,
    ip_address inet,
    user_agent text,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_sessions OWNER TO cabinet_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: cabinet_user
--

CREATE SEQUENCE public.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_sessions_id_seq OWNER TO cabinet_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cabinet_user
--

ALTER SEQUENCE public.user_sessions_id_seq OWNED BY public.user_sessions.id;


--
-- Name: vaccination_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vaccination_schedules (
    id integer NOT NULL,
    schedule_code character varying(20) NOT NULL,
    patient_id integer NOT NULL,
    vaccine_id integer NOT NULL,
    dose_number integer NOT NULL,
    scheduled_date date NOT NULL,
    administered_date date,
    is_administered boolean DEFAULT false,
    administering_doctor_id integer,
    lot_number character varying(100),
    adverse_reactions text,
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.vaccination_schedules OWNER TO postgres;

--
-- Name: vaccination_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vaccination_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vaccination_schedules_id_seq OWNER TO postgres;

--
-- Name: vaccination_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vaccination_schedules_id_seq OWNED BY public.vaccination_schedules.id;


--
-- Name: vaccines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vaccines (
    id integer NOT NULL,
    vaccine_code character varying(20) NOT NULL,
    vaccine_name character varying(255) NOT NULL,
    manufacturer character varying(255),
    created_by integer NOT NULL,
    updated_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.vaccines OWNER TO postgres;

--
-- Name: vaccines_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vaccines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vaccines_id_seq OWNER TO postgres;

--
-- Name: vaccines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vaccines_id_seq OWNED BY public.vaccines.id;


--
-- Name: visit_services; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.visit_services (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    service_id integer NOT NULL,
    actual_price numeric(10,2),
    performed_by_doctor_id integer,
    notes text,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.visit_services OWNER TO postgres;

--
-- Name: visit_services_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.visit_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.visit_services_id_seq OWNER TO postgres;

--
-- Name: visit_services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.visit_services_id_seq OWNED BY public.visit_services.id;


--
-- Name: visit_symptoms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.visit_symptoms (
    id integer NOT NULL,
    visit_id integer NOT NULL,
    symptom_id integer NOT NULL,
    severity character varying(50),
    duration_days integer,
    notes text,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp with time zone,
    deleted_by integer
);


ALTER TABLE public.visit_symptoms OWNER TO postgres;

--
-- Name: visit_symptoms_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.visit_symptoms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.visit_symptoms_id_seq OWNER TO postgres;

--
-- Name: visit_symptoms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.visit_symptoms_id_seq OWNED BY public.visit_symptoms.id;


--
-- Name: allergies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.allergies ALTER COLUMN id SET DEFAULT nextval('public.allergies_id_seq'::regclass);


--
-- Name: appointment_slots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment_slots ALTER COLUMN id SET DEFAULT nextval('public.appointment_slots_id_seq'::regclass);


--
-- Name: appointments id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments ALTER COLUMN id SET DEFAULT nextval('public.appointments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: banks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks ALTER COLUMN id SET DEFAULT nextval('public.banks_id_seq'::regclass);


--
-- Name: billing_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories ALTER COLUMN id SET DEFAULT nextval('public.billing_categories_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: doctor_specialties id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctor_specialties ALTER COLUMN id SET DEFAULT nextval('public.doctor_specialties_id_seq'::regclass);


--
-- Name: doctors id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors ALTER COLUMN id SET DEFAULT nextval('public.doctors_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: lab_orders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders ALTER COLUMN id SET DEFAULT nextval('public.lab_orders_id_seq'::regclass);


--
-- Name: lab_tests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests ALTER COLUMN id SET DEFAULT nextval('public.lab_tests_id_seq'::regclass);


--
-- Name: medical_certificates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates ALTER COLUMN id SET DEFAULT nextval('public.medical_certificates_id_seq'::regclass);


--
-- Name: medical_conditions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions ALTER COLUMN id SET DEFAULT nextval('public.medical_conditions_id_seq'::regclass);


--
-- Name: medical_reports id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports ALTER COLUMN id SET DEFAULT nextval('public.medical_reports_id_seq'::regclass);


--
-- Name: medical_services id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services ALTER COLUMN id SET DEFAULT nextval('public.medical_services_id_seq'::regclass);


--
-- Name: medications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications ALTER COLUMN id SET DEFAULT nextval('public.medications_id_seq'::regclass);


--
-- Name: modules id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.modules ALTER COLUMN id SET DEFAULT nextval('public.modules_id_seq'::regclass);


--
-- Name: patient_allergies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies ALTER COLUMN id SET DEFAULT nextval('public.patient_allergies_id_seq'::regclass);


--
-- Name: patient_diagnoses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses ALTER COLUMN id SET DEFAULT nextval('public.patient_diagnoses_id_seq'::regclass);


--
-- Name: patient_payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments ALTER COLUMN id SET DEFAULT nextval('public.patient_payments_id_seq'::regclass);


--
-- Name: patient_visits id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits ALTER COLUMN id SET DEFAULT nextval('public.patient_visits_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: pharmacies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies ALTER COLUMN id SET DEFAULT nextval('public.pharmacies_id_seq'::regclass);


--
-- Name: prescriptions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions ALTER COLUMN id SET DEFAULT nextval('public.prescriptions_id_seq'::regclass);


--
-- Name: radiology_exams id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams ALTER COLUMN id SET DEFAULT nextval('public.radiology_exams_id_seq'::regclass);


--
-- Name: radiology_orders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders ALTER COLUMN id SET DEFAULT nextval('public.radiology_orders_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: staff id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff ALTER COLUMN id SET DEFAULT nextval('public.staff_id_seq'::regclass);


--
-- Name: symptoms id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms ALTER COLUMN id SET DEFAULT nextval('public.symptoms_id_seq'::regclass);


--
-- Name: system_users id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users ALTER COLUMN id SET DEFAULT nextval('public.system_users_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN id SET DEFAULT nextval('public.user_sessions_id_seq'::regclass);


--
-- Name: vaccination_schedules id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules ALTER COLUMN id SET DEFAULT nextval('public.vaccination_schedules_id_seq'::regclass);


--
-- Name: vaccines id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines ALTER COLUMN id SET DEFAULT nextval('public.vaccines_id_seq'::regclass);


--
-- Name: visit_services id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services ALTER COLUMN id SET DEFAULT nextval('public.visit_services_id_seq'::regclass);


--
-- Name: visit_symptoms id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms ALTER COLUMN id SET DEFAULT nextval('public.visit_symptoms_id_seq'::regclass);


--
-- Data for Name: allergies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.allergies (id, allergy_name, allergy_type, description, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: appointment_slots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.appointment_slots (id, slot_index, slot_time, is_available, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: appointments; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.appointments (id, appointment_code, patient_id, doctor_id, appointment_date, appointment_time, appointment_type, status, reason_for_visit, notes, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.audit_logs (id, table_name, record_id, action, old_values, new_values, user_id, ip_address, user_agent, created_at) FROM stdin;
31	staff	1	UPDATE	{"id": 1, "fax": null, "city": null, "email": "admin@hospital.com", "gender": null, "region": null, "country": null, "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "IT", "first_name": "System", "home_phone": null, "updated_at": "2025-09-28T18:14:14.482419+01:00", "updated_by": null, "mobile_phone": null, "date_of_birth": null, "profile_image": null, "marital_status": null}	{"id": 1, "fax": null, "city": null, "email": "admin@hospital.com", "gender": null, "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "IT", "first_name": "System", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:06:09.497573+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": null, "profile_image": null, "marital_status": null}	\N	\N	\N	2025-10-04 14:06:09.497573+01
32	staff	1	UPDATE	{"id": 1, "fax": null, "city": null, "email": "admin@hospital.com", "gender": null, "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "IT", "first_name": "System", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:06:09.497573+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": null, "profile_image": null, "marital_status": null}	{"id": 1, "fax": null, "city": null, "email": "admin@hospital.com", "gender": null, "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "IT", "first_name": "System", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:13:24.329018+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": null, "profile_image": null, "marital_status": null}	\N	\N	\N	2025-10-04 14:13:24.329018+01
33	staff	1	UPDATE	{"id": 1, "fax": null, "city": null, "email": "admin@hospital.com", "gender": null, "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "IT", "first_name": "System", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:13:24.329018+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": null, "profile_image": null, "marital_status": null}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:14:12.120841+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:14:12.120841+01
34	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:14:12.120841+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:14:25.434866+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:14:25.434866+01
35	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:14:25.434866+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:16:07.373415+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:16:07.373415+01
36	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": null, "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:16:07.373415+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "dfvdfv", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:23:53.579604+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:23:53.579604+01
37	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "dfvdfv", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:23:53.579604+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:24:14.748434+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:24:14.748434+01
38	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Pediatrics", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:24:14.748434+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "General Medicine", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:27:59.312151+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 14:27:59.312151+01
39	system_users	1	UPDATE	{"id": 1, "role_id": 1, "staff_id": 1, "username": "superadmin", "is_active": true, "created_at": "2025-09-28T18:14:14.484538+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "last_login": null, "updated_at": "2025-09-28T18:14:14.484538+01:00", "updated_by": null, "locked_until": null, "password_hash": "$2b$12$.GOwHSdLUQPBvUO27ZqNH..L7CfIQGXO39lSbnZxCmRXqkoRZCDUy", "login_attempts": 0, "must_change_password": false}	{"id": 1, "role_id": 1, "staff_id": 1, "username": "superadmin", "is_active": true, "created_at": "2025-09-28T18:14:14.484538+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "last_login": null, "updated_at": "2025-10-04T15:02:14.677864+01:00", "updated_by": null, "locked_until": null, "password_hash": "$2b$12$Eki2T2CM9Mt2DFnbP.axaeTE2drBN68ns80De5k1G42VHCY.ZDTpC", "login_attempts": 0, "must_change_password": false}	\N	\N	\N	2025-10-04 15:02:14.677864+01
40	system_users	1	UPDATE	{"id": 1, "role_id": 1, "staff_id": 1, "username": "superadmin", "is_active": true, "created_at": "2025-09-28T18:14:14.484538+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "last_login": null, "updated_at": "2025-10-04T15:02:14.677864+01:00", "updated_by": null, "locked_until": null, "password_hash": "$2b$12$Eki2T2CM9Mt2DFnbP.axaeTE2drBN68ns80De5k1G42VHCY.ZDTpC", "login_attempts": 0, "must_change_password": false}	{"id": 1, "role_id": 1, "staff_id": 1, "username": "superadmin", "is_active": true, "created_at": "2025-09-28T18:14:14.484538+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "last_login": null, "updated_at": "2025-10-04T15:03:15.594405+01:00", "updated_by": null, "locked_until": null, "password_hash": "$2b$12$2JQc/FD1Bp1AdPk64zg0vuhDMgOhRU..q5gXipa7ramxB/8z37td6", "login_attempts": 0, "must_change_password": false}	\N	\N	\N	2025-10-04 15:03:15.594405+01
41	roles	10	INSERT	\N	{"id": 10, "name": "superadmin", "created_at": "2025-10-04T21:25:46.529988+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:25:46.529988+01:00", "updated_by": 1, "description": "Is the super admin of system"}	\N	\N	\N	2025-10-04 21:25:46.529988+01
42	roles	11	INSERT	\N	{"id": 11, "name": "test", "created_at": "2025-10-04T21:26:12.115656+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:26:12.115656+01:00", "updated_by": 1, "description": "Test description"}	\N	\N	\N	2025-10-04 21:26:12.115656+01
43	roles	11	UPDATE	{"id": 11, "name": "test", "created_at": "2025-10-04T21:26:12.115656+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:26:12.115656+01:00", "updated_by": 1, "description": "Test description"}	{"id": 11, "name": "test1", "created_at": "2025-10-04T21:26:12.115656+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:26:24.998627+01:00", "updated_by": 1, "description": "Test description"}	\N	\N	\N	2025-10-04 21:26:24.998627+01
44	roles	11	UPDATE	{"id": 11, "name": "test1", "created_at": "2025-10-04T21:26:12.115656+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:26:24.998627+01:00", "updated_by": 1, "description": "Test description"}	{"id": 11, "name": "test1", "created_at": "2025-10-04T21:26:12.115656+01:00", "created_by": 1, "deleted_at": "2025-10-04T21:29:50.099056+01:00", "deleted_by": 1, "updated_at": "2025-10-04T21:29:50.099056+01:00", "updated_by": 1, "description": "Test description"}	\N	\N	\N	2025-10-04 21:29:50.099056+01
45	roles	10	UPDATE	{"id": 10, "name": "superadmin", "created_at": "2025-10-04T21:25:46.529988+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:25:46.529988+01:00", "updated_by": 1, "description": "Is the super admin of system"}	{"id": 10, "name": "superadmin", "created_at": "2025-10-04T21:25:46.529988+01:00", "created_by": 1, "deleted_at": "2025-10-04T21:30:00.737636+01:00", "deleted_by": 1, "updated_at": "2025-10-04T21:30:00.737636+01:00", "updated_by": 1, "description": "Is the super admin of system"}	\N	\N	\N	2025-10-04 21:30:00.737636+01
46	roles	13	INSERT	\N	{"id": 13, "name": "test11", "created_at": "2025-10-04T21:42:06.719197+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "updated_at": "2025-10-04T21:42:06.719197+01:00", "updated_by": 1, "description": "Test description"}	\N	\N	\N	2025-10-04 21:42:06.719197+01
47	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "General Medicine", "first_name": "Super", "home_phone": "(000) 000-0000", "updated_at": "2025-10-04T14:27:59.312151+01:00", "updated_by": 1, "mobile_phone": "(000) 000-0000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "General Medicine", "first_name": "Super", "home_phone": "0500000000", "updated_at": "2025-10-04T22:26:45.35725+01:00", "updated_by": 1, "mobile_phone": "0600000000", "date_of_birth": "2001-01-01", "profile_image": null, "marital_status": "single"}	\N	\N	\N	2025-10-04 22:26:45.35725+01
48	staff	4	UPDATE	{"id": 4, "fax": null, "city": null, "email": "mike.brown@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Receptionist", "hire_date": "2021-06-10", "last_name": "Brown", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Administration", "first_name": "Mike", "home_phone": null, "updated_at": "2025-09-28T18:14:14.565163+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": null, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	{"id": 4, "fax": null, "city": null, "email": "mike.brown@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Receptionist", "hire_date": "2021-06-10", "last_name": "Brown", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Administration", "first_name": "Mike", "home_phone": null, "updated_at": "2025-10-05T14:04:45.787571+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": 1, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	\N	\N	\N	2025-10-05 14:04:45.787571+01
49	staff	2	UPDATE	{"id": 2, "fax": null, "city": null, "email": "john.smith@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Doctor", "hire_date": "2020-01-15", "last_name": "Smith", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Cardiology", "first_name": "John", "home_phone": null, "updated_at": "2025-09-28T18:14:14.565163+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": null, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	{"id": 2, "fax": null, "city": null, "email": "john.smith@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Doctor", "hire_date": "2020-01-15", "last_name": "Smith", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Cardiology", "first_name": "John", "home_phone": null, "updated_at": "2025-10-05T14:04:45.787571+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": 2, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	\N	\N	\N	2025-10-05 14:04:45.787571+01
50	staff	3	UPDATE	{"id": 3, "fax": null, "city": null, "email": "sarah.johnson@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Nurse", "hire_date": "2019-03-20", "last_name": "Johnson", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Emergency", "first_name": "Sarah", "home_phone": null, "updated_at": "2025-09-28T18:14:14.565163+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": null, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	{"id": 3, "fax": null, "city": null, "email": "sarah.johnson@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Nurse", "hire_date": "2019-03-20", "last_name": "Johnson", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Emergency", "first_name": "Sarah", "home_phone": null, "updated_at": "2025-10-05T14:04:45.787571+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": 3, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	\N	\N	\N	2025-10-05 14:04:45.787571+01
51	staff	1	UPDATE	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "role_id": null, "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "General Medicine", "first_name": "Super", "home_phone": "0500000000", "updated_at": "2025-10-04T22:26:45.35725+01:00", "updated_by": 1, "doctor_code": null, "mobile_phone": "0600000000", "date_of_birth": "2001-01-01", "department_id": null, "profile_image": null, "license_number": null, "marital_status": "single", "specialization": null}	{"id": 1, "fax": null, "city": "Azilal", "email": "admin@hospital.com", "gender": "M", "region": "rabat-sale-kenitra", "country": "morocco", "role_id": null, "position": "System Administrator", "hire_date": "2025-09-28", "last_name": "Administrator", "created_at": "2025-09-28T18:14:14.482419+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "General Medicine", "first_name": "Super", "home_phone": "0500000000", "updated_at": "2025-10-05T14:04:45.787571+01:00", "updated_by": 1, "doctor_code": null, "mobile_phone": "0600000000", "date_of_birth": "2001-01-01", "department_id": 4, "profile_image": null, "license_number": null, "marital_status": "single", "specialization": null}	\N	\N	\N	2025-10-05 14:04:45.787571+01
52	staff	5	UPDATE	{"id": 5, "fax": null, "city": null, "email": "lisa.davis@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Lab Technician", "hire_date": "2018-11-05", "last_name": "Davis", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Laboratory", "first_name": "Lisa", "home_phone": null, "updated_at": "2025-09-28T18:14:14.565163+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": null, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	{"id": 5, "fax": null, "city": null, "email": "lisa.davis@hospital.com", "gender": null, "region": null, "country": null, "role_id": null, "position": "Lab Technician", "hire_date": "2018-11-05", "last_name": "Davis", "created_at": "2025-09-28T18:14:14.565163+01:00", "created_by": 1, "deleted_at": null, "deleted_by": null, "department": "Laboratory", "first_name": "Lisa", "home_phone": null, "updated_at": "2025-10-05T14:04:45.787571+01:00", "updated_by": null, "doctor_code": null, "mobile_phone": null, "date_of_birth": null, "department_id": 5, "profile_image": null, "license_number": null, "marital_status": null, "specialization": null}	\N	\N	\N	2025-10-05 14:04:45.787571+01
\.


--
-- Data for Name: banks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.banks (id, bank_code, bank_name, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: billing_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.billing_categories (id, category_code, category_name, description, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.departments (id, name, description, head_id, created_by, updated_by, deleted_by, created_at, updated_at, deleted_at) FROM stdin;
1	Administration	\N	\N	1	\N	\N	2025-10-05 14:04:45.787571+01	2025-10-05 14:04:45.787571+01	\N
2	Cardiology	\N	\N	1	\N	\N	2025-10-05 14:04:45.787571+01	2025-10-05 14:04:45.787571+01	\N
3	Emergency	\N	\N	1	\N	\N	2025-10-05 14:04:45.787571+01	2025-10-05 14:04:45.787571+01	\N
4	General Medicine	\N	\N	1	\N	\N	2025-10-05 14:04:45.787571+01	2025-10-05 14:04:45.787571+01	\N
5	Laboratory	\N	\N	1	\N	\N	2025-10-05 14:04:45.787571+01	2025-10-05 14:04:45.787571+01	\N
\.


--
-- Data for Name: doctor_specialties; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.doctor_specialties (id, doctor_id, specialty, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: doctors; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.doctors (id, doctor_code, first_name, last_name, specialization, license_number, email, phone, mobile, address, city, is_active, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
1	DOC001	John	Smith	Cardiology	MED12345	john.smith@hospital.com	+1234567890	\N	\N	\N	t	1	\N	2025-09-28 18:14:14.560657+01	2025-09-28 18:14:14.560657+01	\N	\N
2	DOC002	Emily	Wilson	Pediatrics	PED67890	emily.wilson@hospital.com	+1234567891	\N	\N	\N	t	1	\N	2025-09-28 18:14:14.560657+01	2025-09-28 18:14:14.560657+01	\N	\N
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expenses (id, expense_code, expense_date, amount, category_id, description, payment_method, bank_name, check_number, recorded_by_doctor_id, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: lab_orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lab_orders (id, visit_id, test_id, ordering_doctor_id, order_date, laboratory_name, clinical_notes, results, result_date, is_abnormal, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: lab_tests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lab_tests (id, test_code, test_name, category, description, specimen_type, reference_range_min, reference_range_max, measurement_unit, is_favorite, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: medical_certificates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medical_certificates (id, certificate_code, patient_id, issuing_doctor_id, issue_date, certificate_type, work_resumption_date, accident_date, medical_findings, restrictions, duration_days, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: medical_conditions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medical_conditions (id, condition_code, condition_name, category, icd_code, description, general_information, diagnostic_criteria, treatment_guidelines, is_favorite, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: medical_reports; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medical_reports (id, report_code, patient_id, doctor_id, report_date, report_type, title, content, additional_notes, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: medical_services; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.medical_services (id, service_code, service_name, description, standard_price, is_active, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: medications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medications (id, medication_code, generic_name, brand_name, pharmaceutical_form, dosage_strength, manufacturer, unit_price, is_active, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: modules; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.modules (id, name, description, created_at) FROM stdin;
1	patients	Patient Management Module	2025-09-28 18:06:44.942837+01
2	doctors	Doctor Management Module	2025-09-28 18:06:44.942837+01
3	appointments	Appointment Scheduling Module	2025-09-28 18:06:44.942837+01
4	medical_records	Medical Records Module	2025-09-28 18:06:44.942837+01
5	prescriptions	Prescription Management Module	2025-09-28 18:06:44.942837+01
6	lab_tests	Laboratory Tests Module	2025-09-28 18:06:44.942837+01
7	radiology	Radiology Module	2025-09-28 18:06:44.942837+01
8	billing	Billing and Payments Module	2025-09-28 18:06:44.942837+01
9	inventory	Medical Inventory Module	2025-09-28 18:06:44.942837+01
10	staff	Staff Management Module	2025-09-28 18:06:44.942837+01
11	reports	Reports and Analytics Module	2025-09-28 18:06:44.942837+01
12	system	System Administration Module	2025-09-28 18:06:44.942837+01
\.


--
-- Data for Name: patient_allergies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_allergies (id, patient_id, allergy_id, severity, reaction_description, diagnosed_date, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: patient_diagnoses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_diagnoses (id, visit_id, condition_id, diagnosis_date, diagnosing_doctor_id, certainty_level, notes, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: patient_payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_payments (id, payment_code, visit_id, payment_date, amount, payment_method, bank_name, check_number, notes, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: patient_visits; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.patient_visits (id, visit_code, patient_id, doctor_id, visit_date, visit_time, visit_type, chief_complaint, diagnosis, clinical_notes, weight, height, blood_pressure_systolic, blood_pressure_diastolic, blood_glucose, temperature, status, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.patients (id, patient_code, first_name, last_name, date_of_birth, gender, marital_status, blood_type, place_of_birth, medical_history, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
1	PAT001	Alice	Brown	1985-03-15	female	\N	A+	\N	\N	1	\N	2025-09-28 18:14:14.562721+01	2025-09-28 18:14:14.562721+01	\N	\N
2	PAT002	Bob	Wilson	1978-07-22	male	\N	O+	\N	\N	1	\N	2025-09-28 18:14:14.562721+01	2025-09-28 18:14:14.562721+01	\N	\N
3	PAT003	Carol	Davis	1990-12-10	female	\N	B-	\N	\N	1	\N	2025-09-28 18:14:14.562721+01	2025-09-28 18:14:14.562721+01	\N	\N
\.


--
-- Data for Name: pharmacies; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pharmacies (id, pharmacy_code, pharmacy_name, owner_name, address, city, phone, mobile, email, is_active, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: prescriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prescriptions (id, visit_id, medication_id, prescribing_doctor_id, dosage_instructions, quantity_prescribed, duration_days, is_free, refills_allowed, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: radiology_exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.radiology_exams (id, exam_code, exam_name, category, exam_type, is_favorite, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: radiology_orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.radiology_orders (id, visit_id, exam_id, ordering_doctor_id, order_date, imaging_center, clinical_notes, radiology_report, findings, conclusion, report_date, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.role_permissions (id, role_id, module_id, can_create, can_read, can_update, can_delete, can_export, can_manage_users, created_by, updated_by, created_at, updated_at) FROM stdin;
1	1	1	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
2	1	2	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
3	1	3	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
4	1	4	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
5	1	5	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
6	1	6	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
7	1	7	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
8	1	8	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
9	1	9	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
10	1	10	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
11	1	11	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
12	1	12	t	t	t	t	t	t	1	\N	2025-09-28 18:14:14.456752+01	2025-09-28 18:23:49.212869+01
13	2	1	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
14	2	2	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
15	2	3	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
16	2	4	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
17	2	5	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
18	2	6	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
19	2	7	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
20	2	8	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
21	2	9	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
22	2	10	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
23	2	11	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.462016+01	2025-09-28 18:23:49.212869+01
24	2	12	f	t	f	f	f	f	1	\N	2025-09-28 18:14:14.464032+01	2025-09-28 18:23:49.212869+01
25	3	1	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
26	3	3	t	t	t	f	f	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
27	3	4	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
28	3	5	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
29	3	6	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
30	3	7	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
31	3	11	f	t	f	f	t	f	1	\N	2025-09-28 18:14:14.465512+01	2025-09-28 18:23:49.212869+01
32	4	1	t	t	t	f	f	f	1	\N	2025-09-28 18:14:14.469475+01	2025-09-28 18:23:49.212869+01
33	4	3	t	t	t	f	f	f	1	\N	2025-09-28 18:14:14.469475+01	2025-09-28 18:23:49.212869+01
34	4	4	t	t	f	f	f	f	1	\N	2025-09-28 18:14:14.469475+01	2025-09-28 18:23:49.212869+01
35	4	5	f	t	f	f	f	f	1	\N	2025-09-28 18:14:14.469475+01	2025-09-28 18:23:49.212869+01
36	6	1	t	t	t	f	f	f	1	\N	2025-09-28 18:14:14.473145+01	2025-09-28 18:23:49.212869+01
37	6	3	t	t	t	t	f	f	1	\N	2025-09-28 18:14:14.473145+01	2025-09-28 18:23:49.212869+01
38	6	8	t	t	t	f	f	f	1	\N	2025-09-28 18:14:14.473145+01	2025-09-28 18:23:49.212869+01
39	5	1	f	t	f	f	f	f	1	\N	2025-09-28 18:14:14.475903+01	2025-09-28 18:23:49.212869+01
40	5	6	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.475903+01	2025-09-28 18:23:49.212869+01
41	5	4	f	t	t	f	f	f	1	\N	2025-09-28 18:14:14.475903+01	2025-09-28 18:23:49.212869+01
42	7	1	f	t	f	f	f	f	1	\N	2025-09-28 18:14:14.478033+01	2025-09-28 18:23:49.212869+01
43	7	8	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.478033+01	2025-09-28 18:23:49.212869+01
44	7	11	f	t	f	f	t	f	1	\N	2025-09-28 18:14:14.478033+01	2025-09-28 18:23:49.212869+01
45	8	1	f	t	f	f	f	f	1	\N	2025-09-28 18:14:14.47979+01	2025-09-28 18:23:49.212869+01
46	8	5	t	t	t	f	t	f	1	\N	2025-09-28 18:14:14.47979+01	2025-09-28 18:23:49.212869+01
47	8	9	t	t	t	t	t	f	1	\N	2025-09-28 18:14:14.47979+01	2025-09-28 18:23:49.212869+01
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.roles (id, name, description, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
1	superadmin	Full system access with user management privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
2	admin	Administrative access with most system privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
3	doctor	Medical professional with patient care privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
4	nurse	Nursing staff with limited medical privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
5	lab_technician	Laboratory staff with test management privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
6	receptionist	Front desk staff with scheduling privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
7	accountant	Billing and financial staff	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
8	pharmacist	Pharmacy staff with medication privileges	1	\N	2025-09-28 18:14:14.453566+01	2025-09-28 18:14:14.453566+01	\N	\N
11	test1	Test description	1	1	2025-10-04 21:26:12.115656+01	2025-10-04 21:29:50.099056+01	2025-10-04 21:29:50.099056+01	1
10	superadmin	Is the super admin of system	1	1	2025-10-04 21:25:46.529988+01	2025-10-04 21:30:00.737636+01	2025-10-04 21:30:00.737636+01	1
13	test11	Test description	1	1	2025-10-04 21:42:06.719197+01	2025-10-04 21:42:06.719197+01	\N	\N
\.


--
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.staff (id, first_name, last_name, date_of_birth, gender, marital_status, mobile_phone, home_phone, fax, email, country, region, city, profile_image, "position", hire_date, department, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by, department_id, role_id, doctor_code, specialization, license_number) FROM stdin;
4	Mike	Brown	\N	\N	\N	\N	\N	\N	mike.brown@hospital.com	\N	\N	\N	\N	Receptionist	2021-06-10	Administration	1	\N	2025-09-28 18:14:14.565163+01	2025-10-05 14:04:45.787571+01	\N	\N	1	\N	\N	\N	\N
2	John	Smith	\N	\N	\N	\N	\N	\N	john.smith@hospital.com	\N	\N	\N	\N	Doctor	2020-01-15	Cardiology	1	\N	2025-09-28 18:14:14.565163+01	2025-10-05 14:04:45.787571+01	\N	\N	2	\N	\N	\N	\N
3	Sarah	Johnson	\N	\N	\N	\N	\N	\N	sarah.johnson@hospital.com	\N	\N	\N	\N	Nurse	2019-03-20	Emergency	1	\N	2025-09-28 18:14:14.565163+01	2025-10-05 14:04:45.787571+01	\N	\N	3	\N	\N	\N	\N
1	Super	Administrator	2001-01-01	M	single	0600000000	0500000000	\N	admin@hospital.com	morocco	rabat-sale-kenitra	Azilal	\N	System Administrator	2025-09-28	General Medicine	1	1	2025-09-28 18:14:14.482419+01	2025-10-05 14:04:45.787571+01	\N	\N	4	\N	\N	\N	\N
5	Lisa	Davis	\N	\N	\N	\N	\N	\N	lisa.davis@hospital.com	\N	\N	\N	\N	Lab Technician	2018-11-05	Laboratory	1	\N	2025-09-28 18:14:14.565163+01	2025-10-05 14:04:45.787571+01	\N	\N	5	\N	\N	\N	\N
\.


--
-- Data for Name: symptoms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.symptoms (id, symptom_code, symptom_name, description, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: system_users; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.system_users (id, staff_id, username, password_hash, role_id, is_active, last_login, must_change_password, login_attempts, locked_until, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
2	2	jsmith	$2b$12$LQv3c1yqBWVHxkd0g8f7O.FfG2c3Q7p8x8UZ8bR8X8N8eJ8vR8X8O	3	t	\N	f	0	\N	1	\N	2025-09-28 18:14:14.566554+01	2025-09-28 18:14:14.566554+01	\N	\N
3	3	sjohnson	$2b$12$LQv3c1yqBWVHxkd0g8f7O.FfG2c3Q7p8x8UZ8bR8X8N8eJ8vR8X8O	4	t	\N	f	0	\N	1	\N	2025-09-28 18:14:14.566554+01	2025-09-28 18:14:14.566554+01	\N	\N
4	4	mbrown	$2b$12$LQv3c1yqBWVHxkd0g8f7O.FfG2c3Q7p8x8UZ8bR8X8N8eJ8vR8X8O	6	t	\N	f	0	\N	1	\N	2025-09-28 18:14:14.566554+01	2025-09-28 18:14:14.566554+01	\N	\N
5	5	ldavis	$2b$12$LQv3c1yqBWVHxkd0g8f7O.FfG2c3Q7p8x8UZ8bR8X8N8eJ8vR8X8O	5	t	\N	f	0	\N	1	\N	2025-09-28 18:14:14.566554+01	2025-09-28 18:14:14.566554+01	\N	\N
1	1	superadmin	$2b$12$2JQc/FD1Bp1AdPk64zg0vuhDMgOhRU..q5gXipa7ramxB/8z37td6	1	t	\N	f	0	\N	1	\N	2025-09-28 18:14:14.484538+01	2025-10-04 15:03:15.594405+01	\N	\N
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: cabinet_user
--

COPY public.user_sessions (id, user_id, session_token, ip_address, user_agent, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: vaccination_schedules; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vaccination_schedules (id, schedule_code, patient_id, vaccine_id, dose_number, scheduled_date, administered_date, is_administered, administering_doctor_id, lot_number, adverse_reactions, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: vaccines; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vaccines (id, vaccine_code, vaccine_name, manufacturer, created_by, updated_by, created_at, updated_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: visit_services; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.visit_services (id, visit_id, service_id, actual_price, performed_by_doctor_id, notes, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: visit_symptoms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.visit_symptoms (id, visit_id, symptom_id, severity, duration_days, notes, created_by, created_at, deleted_at, deleted_by) FROM stdin;
\.


--
-- Name: allergies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.allergies_id_seq', 1, false);


--
-- Name: appointment_slots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.appointment_slots_id_seq', 1, false);


--
-- Name: appointments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.appointments_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 52, true);


--
-- Name: banks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.banks_id_seq', 1, false);


--
-- Name: billing_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.billing_categories_id_seq', 1, false);


--
-- Name: departments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.departments_id_seq', 5, true);


--
-- Name: doctor_specialties_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.doctor_specialties_id_seq', 1, false);


--
-- Name: doctors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.doctors_id_seq', 4, true);


--
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expenses_id_seq', 1, false);


--
-- Name: lab_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lab_orders_id_seq', 1, false);


--
-- Name: lab_tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lab_tests_id_seq', 1, false);


--
-- Name: medical_certificates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medical_certificates_id_seq', 1, false);


--
-- Name: medical_conditions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medical_conditions_id_seq', 1, false);


--
-- Name: medical_reports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medical_reports_id_seq', 1, false);


--
-- Name: medical_services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.medical_services_id_seq', 1, false);


--
-- Name: medications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medications_id_seq', 1, false);


--
-- Name: modules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.modules_id_seq', 14, true);


--
-- Name: patient_allergies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_allergies_id_seq', 1, false);


--
-- Name: patient_diagnoses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_diagnoses_id_seq', 1, false);


--
-- Name: patient_payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_payments_id_seq', 1, false);


--
-- Name: patient_visits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.patient_visits_id_seq', 1, false);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.patients_id_seq', 5, true);


--
-- Name: pharmacies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pharmacies_id_seq', 1, false);


--
-- Name: prescriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.prescriptions_id_seq', 1, false);


--
-- Name: radiology_exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.radiology_exams_id_seq', 1, false);


--
-- Name: radiology_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.radiology_orders_id_seq', 1, false);


--
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 56, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.roles_id_seq', 14, true);


--
-- Name: staff_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.staff_id_seq', 22, true);


--
-- Name: symptoms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.symptoms_id_seq', 1, false);


--
-- Name: system_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.system_users_id_seq', 10, true);


--
-- Name: user_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cabinet_user
--

SELECT pg_catalog.setval('public.user_sessions_id_seq', 1, false);


--
-- Name: vaccination_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vaccination_schedules_id_seq', 1, false);


--
-- Name: vaccines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vaccines_id_seq', 1, false);


--
-- Name: visit_services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.visit_services_id_seq', 1, false);


--
-- Name: visit_symptoms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.visit_symptoms_id_seq', 1, false);


--
-- Name: allergies allergies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.allergies
    ADD CONSTRAINT allergies_pkey PRIMARY KEY (id);


--
-- Name: appointment_slots appointment_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment_slots
    ADD CONSTRAINT appointment_slots_pkey PRIMARY KEY (id);


--
-- Name: appointments appointments_appointment_code_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_appointment_code_key UNIQUE (appointment_code);


--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: banks banks_bank_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks
    ADD CONSTRAINT banks_bank_code_key UNIQUE (bank_code);


--
-- Name: banks banks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks
    ADD CONSTRAINT banks_pkey PRIMARY KEY (id);


--
-- Name: billing_categories billing_categories_category_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories
    ADD CONSTRAINT billing_categories_category_code_key UNIQUE (category_code);


--
-- Name: billing_categories billing_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories
    ADD CONSTRAINT billing_categories_pkey PRIMARY KEY (id);


--
-- Name: departments departments_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_name_key UNIQUE (name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: doctor_specialties doctor_specialties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctor_specialties
    ADD CONSTRAINT doctor_specialties_pkey PRIMARY KEY (id);


--
-- Name: doctors doctors_doctor_code_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_doctor_code_key UNIQUE (doctor_code);


--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_expense_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_expense_code_key UNIQUE (expense_code);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: lab_orders lab_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_pkey PRIMARY KEY (id);


--
-- Name: lab_tests lab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_pkey PRIMARY KEY (id);


--
-- Name: lab_tests lab_tests_test_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_test_code_key UNIQUE (test_code);


--
-- Name: medical_certificates medical_certificates_certificate_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_certificate_code_key UNIQUE (certificate_code);


--
-- Name: medical_certificates medical_certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_pkey PRIMARY KEY (id);


--
-- Name: medical_conditions medical_conditions_condition_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions
    ADD CONSTRAINT medical_conditions_condition_code_key UNIQUE (condition_code);


--
-- Name: medical_conditions medical_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions
    ADD CONSTRAINT medical_conditions_pkey PRIMARY KEY (id);


--
-- Name: medical_reports medical_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_pkey PRIMARY KEY (id);


--
-- Name: medical_reports medical_reports_report_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_report_code_key UNIQUE (report_code);


--
-- Name: medical_services medical_services_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services
    ADD CONSTRAINT medical_services_pkey PRIMARY KEY (id);


--
-- Name: medical_services medical_services_service_code_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services
    ADD CONSTRAINT medical_services_service_code_key UNIQUE (service_code);


--
-- Name: medications medications_medication_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_medication_code_key UNIQUE (medication_code);


--
-- Name: medications medications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_pkey PRIMARY KEY (id);


--
-- Name: modules modules_name_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_name_key UNIQUE (name);


--
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- Name: patient_allergies patient_allergies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT patient_allergies_pkey PRIMARY KEY (id);


--
-- Name: patient_diagnoses patient_diagnoses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_pkey PRIMARY KEY (id);


--
-- Name: patient_payments patient_payments_payment_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments
    ADD CONSTRAINT patient_payments_payment_code_key UNIQUE (payment_code);


--
-- Name: patient_payments patient_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments
    ADD CONSTRAINT patient_payments_pkey PRIMARY KEY (id);


--
-- Name: patient_visits patient_visits_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_pkey PRIMARY KEY (id);


--
-- Name: patient_visits patient_visits_visit_code_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_visit_code_key UNIQUE (visit_code);


--
-- Name: patients patients_patient_code_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_patient_code_key UNIQUE (patient_code);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: pharmacies pharmacies_pharmacy_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies
    ADD CONSTRAINT pharmacies_pharmacy_code_key UNIQUE (pharmacy_code);


--
-- Name: pharmacies pharmacies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies
    ADD CONSTRAINT pharmacies_pkey PRIMARY KEY (id);


--
-- Name: prescriptions prescriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_pkey PRIMARY KEY (id);


--
-- Name: radiology_exams radiology_exams_exam_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams
    ADD CONSTRAINT radiology_exams_exam_code_key UNIQUE (exam_code);


--
-- Name: radiology_exams radiology_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams
    ADD CONSTRAINT radiology_exams_pkey PRIMARY KEY (id);


--
-- Name: radiology_orders radiology_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_role_id_module_id_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_module_id_key UNIQUE (role_id, module_id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: staff staff_doctor_code_unique; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_doctor_code_unique UNIQUE (doctor_code);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (id);


--
-- Name: symptoms symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_pkey PRIMARY KEY (id);


--
-- Name: symptoms symptoms_symptom_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_symptom_code_key UNIQUE (symptom_code);


--
-- Name: system_users system_users_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_pkey PRIMARY KEY (id);


--
-- Name: system_users system_users_staff_id_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_staff_id_key UNIQUE (staff_id);


--
-- Name: system_users system_users_username_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_username_key UNIQUE (username);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_token_key UNIQUE (session_token);


--
-- Name: vaccination_schedules vaccination_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_pkey PRIMARY KEY (id);


--
-- Name: vaccination_schedules vaccination_schedules_schedule_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_schedule_code_key UNIQUE (schedule_code);


--
-- Name: vaccines vaccines_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines
    ADD CONSTRAINT vaccines_pkey PRIMARY KEY (id);


--
-- Name: vaccines vaccines_vaccine_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines
    ADD CONSTRAINT vaccines_vaccine_code_key UNIQUE (vaccine_code);


--
-- Name: visit_services visit_services_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_pkey PRIMARY KEY (id);


--
-- Name: visit_symptoms visit_symptoms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms
    ADD CONSTRAINT visit_symptoms_pkey PRIMARY KEY (id);


--
-- Name: idx_appointments_created_by; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_appointments_created_by ON public.appointments USING btree (created_by);


--
-- Name: idx_appointments_date; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_appointments_date ON public.appointments USING btree (appointment_date);


--
-- Name: idx_appointments_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_appointments_deleted_at ON public.appointments USING btree (deleted_at);


--
-- Name: idx_appointments_doctor_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_appointments_doctor_id ON public.appointments USING btree (doctor_id);


--
-- Name: idx_appointments_patient_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_appointments_patient_id ON public.appointments USING btree (patient_id);


--
-- Name: idx_audit_logs_created_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_table_record; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_audit_logs_table_record ON public.audit_logs USING btree (table_name, record_id);


--
-- Name: idx_audit_logs_user_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: idx_departments_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_departments_deleted_at ON public.departments USING btree (deleted_at);


--
-- Name: idx_departments_head_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_departments_head_id ON public.departments USING btree (head_id);


--
-- Name: idx_doctors_created_by; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_doctors_created_by ON public.doctors USING btree (created_by);


--
-- Name: idx_doctors_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_doctors_deleted_at ON public.doctors USING btree (deleted_at);


--
-- Name: idx_lab_orders_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lab_orders_created_by ON public.lab_orders USING btree (created_by);


--
-- Name: idx_lab_orders_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lab_orders_deleted_at ON public.lab_orders USING btree (deleted_at);


--
-- Name: idx_lab_orders_visit_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lab_orders_visit_id ON public.lab_orders USING btree (visit_id);


--
-- Name: idx_patient_allergies_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_allergies_created_by ON public.patient_allergies USING btree (created_by);


--
-- Name: idx_patient_allergies_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_allergies_deleted_at ON public.patient_allergies USING btree (deleted_at);


--
-- Name: idx_patient_allergies_patient_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_allergies_patient_id ON public.patient_allergies USING btree (patient_id);


--
-- Name: idx_patient_diagnoses_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_diagnoses_created_by ON public.patient_diagnoses USING btree (created_by);


--
-- Name: idx_patient_diagnoses_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_diagnoses_deleted_at ON public.patient_diagnoses USING btree (deleted_at);


--
-- Name: idx_patient_diagnoses_visit_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_patient_diagnoses_visit_id ON public.patient_diagnoses USING btree (visit_id);


--
-- Name: idx_patient_visits_created_by; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patient_visits_created_by ON public.patient_visits USING btree (created_by);


--
-- Name: idx_patient_visits_date; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patient_visits_date ON public.patient_visits USING btree (visit_date);


--
-- Name: idx_patient_visits_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patient_visits_deleted_at ON public.patient_visits USING btree (deleted_at);


--
-- Name: idx_patient_visits_doctor_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patient_visits_doctor_id ON public.patient_visits USING btree (doctor_id);


--
-- Name: idx_patient_visits_patient_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patient_visits_patient_id ON public.patient_visits USING btree (patient_id);


--
-- Name: idx_patients_created_by; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patients_created_by ON public.patients USING btree (created_by);


--
-- Name: idx_patients_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_patients_deleted_at ON public.patients USING btree (deleted_at);


--
-- Name: idx_prescriptions_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_prescriptions_created_by ON public.prescriptions USING btree (created_by);


--
-- Name: idx_prescriptions_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_prescriptions_deleted_at ON public.prescriptions USING btree (deleted_at);


--
-- Name: idx_prescriptions_visit_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_prescriptions_visit_id ON public.prescriptions USING btree (visit_id);


--
-- Name: idx_radiology_orders_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_radiology_orders_created_by ON public.radiology_orders USING btree (created_by);


--
-- Name: idx_radiology_orders_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_radiology_orders_deleted_at ON public.radiology_orders USING btree (deleted_at);


--
-- Name: idx_radiology_orders_visit_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_radiology_orders_visit_id ON public.radiology_orders USING btree (visit_id);


--
-- Name: idx_role_permissions_role_module; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_role_permissions_role_module ON public.role_permissions USING btree (role_id, module_id);


--
-- Name: idx_roles_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_roles_deleted_at ON public.roles USING btree (deleted_at);


--
-- Name: idx_staff_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_staff_deleted_at ON public.staff USING btree (deleted_at);


--
-- Name: idx_staff_department; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_staff_department ON public.staff USING btree (department);


--
-- Name: idx_staff_department_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_staff_department_id ON public.staff USING btree (department_id);


--
-- Name: idx_staff_position; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_staff_position ON public.staff USING btree ("position");


--
-- Name: idx_staff_role_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_staff_role_id ON public.staff USING btree (role_id);


--
-- Name: idx_system_users_deleted_at; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_system_users_deleted_at ON public.system_users USING btree (deleted_at);


--
-- Name: idx_system_users_role_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_system_users_role_id ON public.system_users USING btree (role_id);


--
-- Name: idx_system_users_staff_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_system_users_staff_id ON public.system_users USING btree (staff_id);


--
-- Name: idx_system_users_username; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_system_users_username ON public.system_users USING btree (username);


--
-- Name: idx_user_sessions_token; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_user_sessions_token ON public.user_sessions USING btree (session_token);


--
-- Name: idx_user_sessions_user_id; Type: INDEX; Schema: public; Owner: cabinet_user
--

CREATE INDEX idx_user_sessions_user_id ON public.user_sessions USING btree (user_id);


--
-- Name: idx_visit_services_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_visit_services_created_by ON public.visit_services USING btree (created_by);


--
-- Name: idx_visit_services_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_visit_services_deleted_at ON public.visit_services USING btree (deleted_at);


--
-- Name: idx_visit_services_visit_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_visit_services_visit_id ON public.visit_services USING btree (visit_id);


--
-- Name: appointments audit_appointments; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_appointments AFTER INSERT OR DELETE OR UPDATE ON public.appointments FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: doctors audit_doctors; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_doctors AFTER INSERT OR DELETE OR UPDATE ON public.doctors FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: patient_visits audit_patient_visits; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_patient_visits AFTER INSERT OR DELETE OR UPDATE ON public.patient_visits FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: patients audit_patients; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_patients AFTER INSERT OR DELETE OR UPDATE ON public.patients FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: prescriptions audit_prescriptions; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER audit_prescriptions AFTER INSERT OR DELETE OR UPDATE ON public.prescriptions FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: roles audit_roles; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_roles AFTER INSERT OR DELETE OR UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: staff audit_staff; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_staff AFTER INSERT OR DELETE OR UPDATE ON public.staff FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: system_users audit_system_users; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER audit_system_users AFTER INSERT OR DELETE OR UPDATE ON public.system_users FOR EACH ROW EXECUTE FUNCTION public.log_audit_event();


--
-- Name: allergies set_allergies_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_allergies_audit_fields BEFORE INSERT OR UPDATE ON public.allergies FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: appointment_slots set_appointment_slots_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_appointment_slots_audit_fields BEFORE INSERT OR UPDATE ON public.appointment_slots FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: appointments set_appointments_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_appointments_audit_fields BEFORE INSERT OR UPDATE ON public.appointments FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: doctors set_doctors_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_doctors_audit_fields BEFORE INSERT OR UPDATE ON public.doctors FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: lab_orders set_lab_orders_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_lab_orders_audit_fields BEFORE INSERT OR UPDATE ON public.lab_orders FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: lab_tests set_lab_tests_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_lab_tests_audit_fields BEFORE INSERT OR UPDATE ON public.lab_tests FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: medical_conditions set_medical_conditions_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_medical_conditions_audit_fields BEFORE INSERT OR UPDATE ON public.medical_conditions FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: medical_services set_medical_services_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_medical_services_audit_fields BEFORE INSERT OR UPDATE ON public.medical_services FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: medications set_medications_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_medications_audit_fields BEFORE INSERT OR UPDATE ON public.medications FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: patient_visits set_patient_visits_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_patient_visits_audit_fields BEFORE INSERT OR UPDATE ON public.patient_visits FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: patients set_patients_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_patients_audit_fields BEFORE INSERT OR UPDATE ON public.patients FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: pharmacies set_pharmacies_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_pharmacies_audit_fields BEFORE INSERT OR UPDATE ON public.pharmacies FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: radiology_exams set_radiology_exams_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_radiology_exams_audit_fields BEFORE INSERT OR UPDATE ON public.radiology_exams FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: radiology_orders set_radiology_orders_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_radiology_orders_audit_fields BEFORE INSERT OR UPDATE ON public.radiology_orders FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: role_permissions set_role_permissions_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_role_permissions_audit_fields BEFORE INSERT OR UPDATE ON public.role_permissions FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: roles set_roles_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_roles_audit_fields BEFORE INSERT OR UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: staff set_staff_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_staff_audit_fields BEFORE INSERT OR UPDATE ON public.staff FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: system_users set_system_users_audit_fields; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER set_system_users_audit_fields BEFORE INSERT OR UPDATE ON public.system_users FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: vaccination_schedules set_vaccination_schedules_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_vaccination_schedules_audit_fields BEFORE INSERT OR UPDATE ON public.vaccination_schedules FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: vaccines set_vaccines_audit_fields; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_vaccines_audit_fields BEFORE INSERT OR UPDATE ON public.vaccines FOR EACH ROW EXECUTE FUNCTION public.set_audit_fields();


--
-- Name: doctors soft_delete_doctors; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER soft_delete_doctors BEFORE UPDATE ON public.doctors FOR EACH ROW WHEN (((new.deleted_at IS NOT NULL) AND (old.deleted_at IS NULL))) EXECUTE FUNCTION public.soft_delete_record();


--
-- Name: patients soft_delete_patients; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER soft_delete_patients BEFORE UPDATE ON public.patients FOR EACH ROW WHEN (((new.deleted_at IS NOT NULL) AND (old.deleted_at IS NULL))) EXECUTE FUNCTION public.soft_delete_record();


--
-- Name: staff soft_delete_staff; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER soft_delete_staff BEFORE UPDATE ON public.staff FOR EACH ROW WHEN (((new.deleted_at IS NOT NULL) AND (old.deleted_at IS NULL))) EXECUTE FUNCTION public.soft_delete_record();


--
-- Name: allergies update_allergies_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_allergies_updated_at BEFORE UPDATE ON public.allergies FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: appointment_slots update_appointment_slots_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_appointment_slots_updated_at BEFORE UPDATE ON public.appointment_slots FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: appointments update_appointments_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON public.appointments FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: departments update_departments_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON public.departments FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: doctors update_doctors_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON public.doctors FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: lab_orders update_lab_orders_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_lab_orders_updated_at BEFORE UPDATE ON public.lab_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: lab_tests update_lab_tests_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_lab_tests_updated_at BEFORE UPDATE ON public.lab_tests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: medical_conditions update_medical_conditions_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_medical_conditions_updated_at BEFORE UPDATE ON public.medical_conditions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: medical_services update_medical_services_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_medical_services_updated_at BEFORE UPDATE ON public.medical_services FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: medications update_medications_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_medications_updated_at BEFORE UPDATE ON public.medications FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: patient_visits update_patient_visits_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_patient_visits_updated_at BEFORE UPDATE ON public.patient_visits FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: patients update_patients_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON public.patients FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: pharmacies update_pharmacies_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_pharmacies_updated_at BEFORE UPDATE ON public.pharmacies FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: radiology_exams update_radiology_exams_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_radiology_exams_updated_at BEFORE UPDATE ON public.radiology_exams FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: radiology_orders update_radiology_orders_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_radiology_orders_updated_at BEFORE UPDATE ON public.radiology_orders FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: role_permissions update_role_permissions_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_role_permissions_updated_at BEFORE UPDATE ON public.role_permissions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: roles update_roles_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: staff update_staff_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_staff_updated_at BEFORE UPDATE ON public.staff FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: system_users update_system_users_updated_at; Type: TRIGGER; Schema: public; Owner: cabinet_user
--

CREATE TRIGGER update_system_users_updated_at BEFORE UPDATE ON public.system_users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: vaccination_schedules update_vaccination_schedules_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_vaccination_schedules_updated_at BEFORE UPDATE ON public.vaccination_schedules FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: vaccines update_vaccines_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_vaccines_updated_at BEFORE UPDATE ON public.vaccines FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: allergies allergies_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.allergies
    ADD CONSTRAINT allergies_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: allergies allergies_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.allergies
    ADD CONSTRAINT allergies_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: allergies allergies_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.allergies
    ADD CONSTRAINT allergies_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: appointment_slots appointment_slots_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment_slots
    ADD CONSTRAINT appointment_slots_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: appointment_slots appointment_slots_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment_slots
    ADD CONSTRAINT appointment_slots_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: appointment_slots appointment_slots_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment_slots
    ADD CONSTRAINT appointment_slots_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: appointments appointments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: appointments appointments_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: appointments appointments_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: appointments appointments_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: appointments appointments_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.system_users(id);


--
-- Name: banks banks_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks
    ADD CONSTRAINT banks_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: banks banks_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks
    ADD CONSTRAINT banks_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: banks banks_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banks
    ADD CONSTRAINT banks_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: billing_categories billing_categories_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories
    ADD CONSTRAINT billing_categories_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: billing_categories billing_categories_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories
    ADD CONSTRAINT billing_categories_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: billing_categories billing_categories_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_categories
    ADD CONSTRAINT billing_categories_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: doctor_specialties doctor_specialties_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctor_specialties
    ADD CONSTRAINT doctor_specialties_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: doctor_specialties doctor_specialties_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctor_specialties
    ADD CONSTRAINT doctor_specialties_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: doctor_specialties doctor_specialties_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctor_specialties
    ADD CONSTRAINT doctor_specialties_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: doctors doctors_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: doctors doctors_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: doctors doctors_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: expenses expenses_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.billing_categories(id) ON DELETE SET NULL;


--
-- Name: expenses expenses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: expenses expenses_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: expenses expenses_recorded_by_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_recorded_by_doctor_id_fkey FOREIGN KEY (recorded_by_doctor_id) REFERENCES public.doctors(id) ON DELETE SET NULL;


--
-- Name: departments fk_department_head; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT fk_department_head FOREIGN KEY (head_id) REFERENCES public.staff(id) ON DELETE SET NULL;


--
-- Name: role_permissions fk_role_permissions_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT fk_role_permissions_updated_by FOREIGN KEY (updated_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: roles fk_roles_deleted_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_deleted_by FOREIGN KEY (deleted_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: roles fk_roles_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_updated_by FOREIGN KEY (updated_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: staff fk_staff_deleted_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT fk_staff_deleted_by FOREIGN KEY (deleted_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: staff fk_staff_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT fk_staff_updated_by FOREIGN KEY (updated_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: system_users fk_system_users_deleted_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT fk_system_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: system_users fk_system_users_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT fk_system_users_updated_by FOREIGN KEY (updated_by) REFERENCES public.system_users(id) ON DELETE SET NULL;


--
-- Name: lab_orders lab_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: lab_orders lab_orders_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: lab_orders lab_orders_ordering_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_ordering_doctor_id_fkey FOREIGN KEY (ordering_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: lab_orders lab_orders_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.lab_tests(id) ON DELETE CASCADE;


--
-- Name: lab_orders lab_orders_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: lab_orders lab_orders_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_orders
    ADD CONSTRAINT lab_orders_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: lab_tests lab_tests_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: lab_tests lab_tests_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: lab_tests lab_tests_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lab_tests
    ADD CONSTRAINT lab_tests_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: medical_certificates medical_certificates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: medical_certificates medical_certificates_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: medical_certificates medical_certificates_issuing_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_issuing_doctor_id_fkey FOREIGN KEY (issuing_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: medical_certificates medical_certificates_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_certificates
    ADD CONSTRAINT medical_certificates_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: medical_conditions medical_conditions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions
    ADD CONSTRAINT medical_conditions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: medical_conditions medical_conditions_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions
    ADD CONSTRAINT medical_conditions_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: medical_conditions medical_conditions_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_conditions
    ADD CONSTRAINT medical_conditions_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: medical_reports medical_reports_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: medical_reports medical_reports_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: medical_reports medical_reports_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: medical_reports medical_reports_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_reports
    ADD CONSTRAINT medical_reports_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: medical_services medical_services_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services
    ADD CONSTRAINT medical_services_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: medical_services medical_services_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services
    ADD CONSTRAINT medical_services_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: medical_services medical_services_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.medical_services
    ADD CONSTRAINT medical_services_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: medications medications_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: medications medications_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: medications medications_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medications
    ADD CONSTRAINT medications_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: patient_allergies patient_allergies_allergy_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT patient_allergies_allergy_id_fkey FOREIGN KEY (allergy_id) REFERENCES public.allergies(id) ON DELETE CASCADE;


--
-- Name: patient_allergies patient_allergies_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT patient_allergies_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: patient_allergies patient_allergies_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT patient_allergies_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: patient_allergies patient_allergies_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_allergies
    ADD CONSTRAINT patient_allergies_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: patient_diagnoses patient_diagnoses_condition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_condition_id_fkey FOREIGN KEY (condition_id) REFERENCES public.medical_conditions(id) ON DELETE CASCADE;


--
-- Name: patient_diagnoses patient_diagnoses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: patient_diagnoses patient_diagnoses_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: patient_diagnoses patient_diagnoses_diagnosing_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_diagnosing_doctor_id_fkey FOREIGN KEY (diagnosing_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: patient_diagnoses patient_diagnoses_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_diagnoses
    ADD CONSTRAINT patient_diagnoses_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: patient_payments patient_payments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments
    ADD CONSTRAINT patient_payments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: patient_payments patient_payments_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments
    ADD CONSTRAINT patient_payments_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: patient_payments patient_payments_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_payments
    ADD CONSTRAINT patient_payments_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: patient_visits patient_visits_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: patient_visits patient_visits_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: patient_visits patient_visits_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: patient_visits patient_visits_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: patient_visits patient_visits_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT patient_visits_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: patients patients_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: patients patients_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: patients patients_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: pharmacies pharmacies_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies
    ADD CONSTRAINT pharmacies_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: pharmacies pharmacies_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies
    ADD CONSTRAINT pharmacies_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: pharmacies pharmacies_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pharmacies
    ADD CONSTRAINT pharmacies_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: prescriptions prescriptions_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: prescriptions prescriptions_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: prescriptions prescriptions_medication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_medication_id_fkey FOREIGN KEY (medication_id) REFERENCES public.medications(id) ON DELETE CASCADE;


--
-- Name: prescriptions prescriptions_prescribing_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_prescribing_doctor_id_fkey FOREIGN KEY (prescribing_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: prescriptions prescriptions_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: radiology_exams radiology_exams_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams
    ADD CONSTRAINT radiology_exams_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: radiology_exams radiology_exams_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams
    ADD CONSTRAINT radiology_exams_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: radiology_exams radiology_exams_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_exams
    ADD CONSTRAINT radiology_exams_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: radiology_orders radiology_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: radiology_orders radiology_orders_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: radiology_orders radiology_orders_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.radiology_exams(id) ON DELETE CASCADE;


--
-- Name: radiology_orders radiology_orders_ordering_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_ordering_doctor_id_fkey FOREIGN KEY (ordering_doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;


--
-- Name: radiology_orders radiology_orders_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: radiology_orders radiology_orders_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.radiology_orders
    ADD CONSTRAINT radiology_orders_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: staff staff_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: staff staff_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE SET NULL;


--
-- Name: symptoms symptoms_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: symptoms symptoms_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: symptoms symptoms_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.symptoms
    ADD CONSTRAINT symptoms_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: system_users system_users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE RESTRICT;


--
-- Name: system_users system_users_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.system_users
    ADD CONSTRAINT system_users_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.staff(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cabinet_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.system_users(id) ON DELETE CASCADE;


--
-- Name: vaccination_schedules vaccination_schedules_administering_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_administering_doctor_id_fkey FOREIGN KEY (administering_doctor_id) REFERENCES public.doctors(id) ON DELETE SET NULL;


--
-- Name: vaccination_schedules vaccination_schedules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: vaccination_schedules vaccination_schedules_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: vaccination_schedules vaccination_schedules_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE CASCADE;


--
-- Name: vaccination_schedules vaccination_schedules_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: vaccination_schedules vaccination_schedules_vaccine_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccination_schedules
    ADD CONSTRAINT vaccination_schedules_vaccine_id_fkey FOREIGN KEY (vaccine_id) REFERENCES public.vaccines(id) ON DELETE CASCADE;


--
-- Name: vaccines vaccines_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines
    ADD CONSTRAINT vaccines_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: vaccines vaccines_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines
    ADD CONSTRAINT vaccines_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: vaccines vaccines_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vaccines
    ADD CONSTRAINT vaccines_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.system_users(id);


--
-- Name: visit_services visit_services_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: visit_services visit_services_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: visit_services visit_services_performed_by_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_performed_by_doctor_id_fkey FOREIGN KEY (performed_by_doctor_id) REFERENCES public.doctors(id) ON DELETE SET NULL;


--
-- Name: visit_services visit_services_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.medical_services(id) ON DELETE CASCADE;


--
-- Name: visit_services visit_services_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_services
    ADD CONSTRAINT visit_services_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: visit_symptoms visit_symptoms_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms
    ADD CONSTRAINT visit_symptoms_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.system_users(id);


--
-- Name: visit_symptoms visit_symptoms_deleted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms
    ADD CONSTRAINT visit_symptoms_deleted_by_fkey FOREIGN KEY (deleted_by) REFERENCES public.system_users(id);


--
-- Name: visit_symptoms visit_symptoms_symptom_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms
    ADD CONSTRAINT visit_symptoms_symptom_id_fkey FOREIGN KEY (symptom_id) REFERENCES public.symptoms(id) ON DELETE CASCADE;


--
-- Name: visit_symptoms visit_symptoms_visit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visit_symptoms
    ADD CONSTRAINT visit_symptoms_visit_id_fkey FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: cabinet_user
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--


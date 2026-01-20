from __future__ import annotations

import smtplib
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


st.set_page_config(page_title="dash", layout="wide")


def init_session_state() -> None:
    """Initialize keys used across the application."""

    defaults = {
        "datasets": {},
        "active_dataset": None,
        "log_entries": [],
        "db_url": "",
        "db_engine": None,
        "smtp_config": {"host": "", "port": 587, "username": "", "use_tls": True},
        "smtp_config": {"host": "", "port": 587, "username": "", "security": "starttls"},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def add_log(message: str) -> None:
    """Record an activity with a timestamp and persist it locally."""

    entry = {"timestamp": datetime.now().isoformat(timespec="seconds"), "message": message}
    st.session_state["log_entries"].append(entry)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    pd.DataFrame(st.session_state["log_entries"]).to_csv(log_dir / "activity_log.csv", index=False)


def load_excel(uploaded_file) -> pd.DataFrame:
    """Return a DataFrame from the uploaded Excel file, allowing sheet selection."""

    excel_file = pd.ExcelFile(uploaded_file)
    sheet_name = st.selectbox("Choose a sheet", excel_file.sheet_names)
    df = excel_file.parse(sheet_name)
    add_log(f"Loaded Excel sheet '{sheet_name}' from {uploaded_file.name} ({len(df)} rows)")
    return df


def set_active_dataset(name: str, df: pd.DataFrame) -> None:
    st.session_state["datasets"][name] = df
    st.session_state["active_dataset"] = name


def current_dataset() -> pd.DataFrame | None:
    active = st.session_state.get("active_dataset")
    if active is None:
        return None
    return st.session_state["datasets"].get(active)


def connect_to_database(url: str) -> Engine | None:
    try:
        engine = create_engine(url)
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        st.session_state["db_url"] = url
        st.session_state["db_engine"] = engine
        add_log("Connected to database")
        return engine
    except SQLAlchemyError as exc:  # noqa: PERF203
        st.error(f"Database connection failed: {exc}")
        return None


def database_table_picker(engine: Engine) -> str | None:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if not tables:
        st.info("No tables found in the database.")
        return None
    return st.selectbox("Available tables", tables)


def render_data_profile(df: pd.DataFrame) -> None:
    st.metric("Rows", len(df))
    st.metric("Columns", len(df.columns))
    st.dataframe(df.describe(include="all").transpose())


def render_visuals(df: pd.DataFrame) -> None:
    st.subheader("Visualize data")
    if df.empty:
        st.info("Upload data to build charts.")
        return

    with st.expander("Chart builder", expanded=True):
        categorical_cols = list(df.select_dtypes(include=["object", "category"]).columns)
        numeric_cols = list(df.select_dtypes(include="number").columns)
        all_columns = list(df.columns)

        x_axis = st.selectbox("X-axis", all_columns, index=0)
        y_axis = st.selectbox("Y-axis", numeric_cols if numeric_cols else all_columns)
        color_by = st.selectbox("Color by (optional)", ["None"] + categorical_cols)
        chart_type = st.radio("Chart type", ["Line", "Bar", "Area"], horizontal=True)

        if chart_type == "Line":
            chart = st.line_chart
        elif chart_type == "Area":
            chart = st.area_chart
        else:
            chart = st.bar_chart

        plot_df = df[[x_axis, y_axis] + ([color_by] if color_by != "None" else [])].dropna()
        if color_by != "None":
            st.caption("Grouping by color column; aggregated counts shown.")
            grouped = plot_df.groupby([x_axis, color_by])[y_axis].mean().unstack(fill_value=0)
            chart(grouped)
        else:
            chart(plot_df.set_index(x_axis)[y_axis])


def render_data_exchange(df: pd.DataFrame, dataset_name: str) -> None:
    st.subheader("Data exchange for other tools")
    if df.empty:
        st.info("Upload data before exporting.")
        return

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name=f"{dataset_name}.csv",
        mime="text/csv",
    )

    if st.button("Write exchange files to exports/", use_container_width=True):
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        csv_path = export_dir / f"{dataset_name}.csv"
        json_path = export_dir / f"{dataset_name}.json"
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient="records", indent=2)
        add_log(f"Saved exchange files to {export_dir}/ for dataset '{dataset_name}'")
        st.success(f"Created {csv_path} and {json_path} for use in other tools.")

    st.caption("Use the exports/ folder as a shared drop point for notebooks, ETL jobs, or BI tools.")


def render_activity_log() -> None:
    st.subheader("Activity log")
    if not st.session_state["log_entries"]:
        st.info("No activity yet. Upload data or connect a database to get started.")
        return
    st.dataframe(pd.DataFrame(st.session_state["log_entries"]))


def send_report_email(
    *,
    df: pd.DataFrame,
    dataset_name: str,
    recipients: list[str],
    subject: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    use_tls: bool,
    attach_csv: bool,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_username or "dash@localhost"
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    if attach_csv:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        msg.add_attachment(
            csv_bytes,
            maintype="text",
            subtype="csv",
            filename=f"{dataset_name}.csv",
        )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if use_tls:
            server.starttls()
        if smtp_username:
            server.login(smtp_username, smtp_password)
        server.send_message(msg)

    add_log(f"Sent report for dataset '{dataset_name}' to {', '.join(recipients)}")
    security: str,
    attach_csv: bool,
) -> None:
    server_cls = smtplib.SMTP_SSL if security == "ssl" else smtplib.SMTP
    with server_cls(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        if security == "starttls":
            server.starttls()
            server.ehlo()
        if smtp_username or smtp_password:
            server.login(smtp_username, smtp_password)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_username or "dash@localhost"
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        if attach_csv:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            msg.add_attachment(
                csv_bytes,
                maintype="text",
                subtype="csv",
                filename=f"{dataset_name}.csv",
            )

        server.send_message(msg)

    add_log(
        f"Sent report for dataset '{dataset_name}' to {', '.join(recipients)} via {security.upper()} on {smtp_host}:{smtp_port}"
    )


def test_smtp_connection(
    *, smtp_host: str, smtp_port: int, smtp_username: str, smtp_password: str, security: str
) -> None:
    server_cls = smtplib.SMTP_SSL if security == "ssl" else smtplib.SMTP
    with server_cls(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo()
        if security == "starttls":
            server.starttls()
            server.ehlo()
        if smtp_username or smtp_password:
            server.login(smtp_username, smtp_password)


def main() -> None:
    init_session_state()
    st.title("dash")
    st.caption("Upload Excel files, explore data, connect a database, and share datasets with other tools.")

    sidebar = st.sidebar
    sidebar.header("Data intake")
    uploaded_file = sidebar.file_uploader("Upload Excel file", type=["xls", "xlsx"])
    dataset_name = sidebar.text_input("Dataset name", value="uploaded_data")

    if uploaded_file:
        df = load_excel(uploaded_file)
        set_active_dataset(dataset_name, df)

    sidebar.header("Database connection (optional)")
    url_input = sidebar.text_input("SQLAlchemy URL", value=st.session_state.get("db_url", ""))
    if sidebar.button("Connect"):
        connect_to_database(url_input)

    if sidebar.button("Load table into workspace", disabled=st.session_state.get("db_engine") is None):
        engine = st.session_state.get("db_engine")
        if engine:
            table = database_table_picker(engine)
            if table:
                try:
                    df = pd.read_sql_table(table, engine)
                    set_active_dataset(table, df)
                    add_log(f"Loaded table '{table}' from database ({len(df)} rows)")
                except SQLAlchemyError as exc:  # noqa: PERF203
                    st.error(f"Could not load table: {exc}")

    df = current_dataset()

    if df is None:
        st.info("Upload an Excel file or load a table from the database to begin.")
        render_activity_log()
        return

    st.success(f"Active dataset: {st.session_state['active_dataset']}")

    with st.expander("Organize your data", expanded=True):
        selected_columns = st.multiselect("Columns to keep", df.columns.tolist(), default=df.columns.tolist())
        filtered_df = df[selected_columns]
        search_term = st.text_input("Quick filter (matches text in any column)")
        if search_term:
            mask = filtered_df.apply(
                lambda col: col.astype(str).str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True)

    render_data_profile(filtered_df)
    render_visuals(filtered_df)

    st.subheader("Database actions")
    engine = st.session_state.get("db_engine")
    if engine:
        table_name = st.text_input("Destination table name", value=f"dash_{st.session_state['active_dataset']}")
        if st.button("Write active dataset to database"):
            try:
                filtered_df.to_sql(table_name, engine, if_exists="replace", index=False)
                add_log(f"Wrote dataset to database table '{table_name}'")
                st.success(f"Saved {len(filtered_df)} rows to table '{table_name}'.")
            except SQLAlchemyError as exc:  # noqa: PERF203
                st.error(f"Could not write dataset: {exc}")
    else:
        st.info("Connect a database in the sidebar to enable writeback.")

    render_data_exchange(filtered_df, st.session_state["active_dataset"])

    with st.expander("Send report", expanded=True):
        st.write("Email a snapshot of the active dataset to collaborators.")
        smtp_state = st.session_state["smtp_config"]
        smtp_host = st.text_input("SMTP host", value=smtp_state.get("host", ""))
        smtp_port = st.number_input("SMTP port", value=int(smtp_state.get("port", 587)), min_value=1, max_value=65535)
        use_tls = st.checkbox("Use STARTTLS", value=bool(smtp_state.get("use_tls", True)))
        security = st.selectbox(
            "Connection security",
            options=["starttls", "ssl", "none"],
            format_func=lambda opt: {"starttls": "STARTTLS", "ssl": "SSL (465)", "none": "None"}.get(opt, opt),
            index=["starttls", "ssl", "none"].index(smtp_state.get("security", "starttls")),
        )
        smtp_username = st.text_input("SMTP username (from)", value=smtp_state.get("username", ""))
        smtp_password = st.text_input("SMTP password", type="password")

        recipients_raw = st.text_input("Recipients (comma-separated)")
        subject = st.text_input("Subject", value=f"dash report - {st.session_state['active_dataset']}")
        default_body = (
            f"Dataset '{st.session_state['active_dataset']}' "
            f"with {len(filtered_df)} rows and {len(filtered_df.columns)} columns.\n"
            f"Columns: {', '.join(filtered_df.columns)}\n\n"
            "Attached: CSV extract of the current view."
        )
        body = st.text_area("Body", value=default_body)
        attach_csv = st.checkbox("Attach CSV extract", value=True)

        if st.button("Send report"):
            recipients = [addr.strip() for addr in recipients_raw.split(",") if addr.strip()]
            if not recipients:
                st.error("Enter at least one recipient.")
            elif not smtp_host:
                st.error("SMTP host is required.")
            else:
                try:
                    send_report_email(
                        df=filtered_df,
                        dataset_name=st.session_state["active_dataset"],
                        recipients=recipients,
                        subject=subject,
                        body=body,
                        smtp_host=smtp_host,
                        smtp_port=int(smtp_port),
                        smtp_username=smtp_username,
                        smtp_password=smtp_password,
                        use_tls=use_tls,
                        security=security,
                        attach_csv=attach_csv,
                    )
                    st.session_state["smtp_config"] = {
                        "host": smtp_host,
                        "port": int(smtp_port),
                        "username": smtp_username,
                        "use_tls": use_tls,
                        "security": security,
                    }
                    st.success(f"Report sent to {', '.join(recipients)}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not send report: {exc}")

    render_activity_log()


if __name__ == "__main__":
    main()

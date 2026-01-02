from __future__ import annotations

from datetime import datetime
from pathlib import Path

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
    render_activity_log()


if __name__ == "__main__":
    main()

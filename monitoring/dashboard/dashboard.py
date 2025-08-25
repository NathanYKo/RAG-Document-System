import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = st.secrets.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "Admin123!")


class DashboardAPI:
    """API client for dashboard data"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the API"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/token",
                data={"username": username, "password": password},
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_dashboard_data(self, days: int = 7) -> Optional[Dict]:
        """Get dashboard data from API"""
        try:
            response = self.session.get(
                f"{self.base_url}/metrics/dashboard?days={days}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch dashboard data: {e}")
            return None

    def get_performance_metrics(self, days: int = 7) -> Optional[Dict]:
        """Get performance metrics from API"""
        try:
            response = self.session.get(
                f"{self.base_url}/metrics/performance?days={days}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch performance metrics: {e}")
            return None

    def get_system_health(self) -> Optional[Dict]:
        """Get system health status"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch system health: {e}")
            return None


def create_performance_charts(dashboard_data: Dict) -> Dict:
    """Create performance visualization charts"""
    performance = dashboard_data["performance_metrics"]

    # KPI Metrics Chart
    kpi_fig = go.Figure()

    metrics = [
        ("Avg Response Time", performance["avg_response_time"], "s"),
        ("Success Rate", performance["success_rate"] * 100, "%"),
        ("Avg Quality Score", performance["avg_quality_score"], "/5"),
        ("User Satisfaction", performance["user_satisfaction"], "/5"),
        ("Retrieval Accuracy", performance["retrieval_accuracy"] * 100, "%"),
    ]

    kpi_fig.add_trace(
        go.Bar(
            x=[m[0] for m in metrics],
            y=[m[1] for m in metrics],
            text=[f"{m[1]:.2f}{m[2]}" for m in metrics],
            textposition="auto",
            marker_color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
        )
    )

    kpi_fig.update_layout(
        title="System Performance KPIs",
        yaxis_title="Value",
        showlegend=False,
        height=400,
    )

    # Query Volume Chart
    query_volume = dashboard_data["query_volume_by_day"]
    volume_fig = px.line(
        x=list(query_volume.keys()),
        y=list(query_volume.values()),
        title="Query Volume Over Time",
        labels={"x": "Date", "y": "Number of Queries"},
    )
    volume_fig.update_traces(line_color="#45B7D1", line_width=3)

    # Feedback Distribution Chart
    feedback_dist = dashboard_data["feedback_distribution"]
    feedback_fig = px.pie(
        values=list(feedback_dist.values()),
        names=[f"{k} Stars" for k in feedback_dist.keys()],
        title="User Feedback Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    return {
        "kpi_chart": kpi_fig,
        "volume_chart": volume_fig,
        "feedback_chart": feedback_fig,
    }


def create_monitoring_charts(performance_data: Dict) -> Dict:
    """Create monitoring-specific charts"""

    # Response Time Distribution (simulated data for demo)
    response_times = [performance_data["avg_response_time"]] * 100  # Simplified
    hist_fig = px.histogram(
        x=response_times,
        title="Response Time Distribution",
        labels={"x": "Response Time (s)", "y": "Frequency"},
        nbins=20,
    )
    hist_fig.update_traces(marker_color="#45B7D1")

    # System Load Gauge
    load_fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=performance_data["success_rate"] * 100,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "System Health Score"},
            delta={"reference": 90},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 80], "color": "yellow"},
                    {"range": [80, 100], "color": "green"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )

    return {"response_time_dist": hist_fig, "system_health_gauge": load_fig}


def render_dashboard():
    """Main dashboard rendering function"""
    st.set_page_config(
        page_title="RAG System Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-healthy { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-error { background-color: #dc3545; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar
    st.sidebar.title("🔧 Dashboard Controls")

    # Authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.api_client = None

    if not st.session_state.authenticated:
        st.sidebar.subheader("🔐 Authentication")
        username = st.sidebar.text_input("Username", value=ADMIN_USERNAME)
        password = st.sidebar.text_input(
            "Password", type="password", value=ADMIN_PASSWORD
        )

        if st.sidebar.button("Login"):
            api_client = DashboardAPI(API_BASE_URL)
            if api_client.authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.api_client = api_client
                st.sidebar.success("✅ Authenticated successfully!")
                st.rerun()
            else:
                st.sidebar.error("❌ Authentication failed")
        return

    # Time range selector
    time_ranges = {
        "Last 24 Hours": 1,
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "Last 90 Days": 90,
    }

    selected_range = st.sidebar.selectbox(
        "📅 Time Range", options=list(time_ranges.keys()), index=1
    )
    days = time_ranges[selected_range]

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.api_client = None
        st.rerun()

    # Main dashboard
    st.title("📊 Enterprise RAG System Dashboard")
    st.markdown(
        f"**Time Range:** {selected_range} | **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()

    # Fetch data
    api_client = st.session_state.api_client

    with st.spinner("Loading dashboard data..."):
        dashboard_data = api_client.get_dashboard_data(days)
        performance_data = api_client.get_performance_metrics(days)
        health_data = api_client.get_system_health()

    if not dashboard_data or not performance_data:
        st.error("❌ Failed to load dashboard data. Please check API connectivity.")
        return

    # System Health Status
    st.subheader("🏥 System Health")
    health_cols = st.columns(4)

    with health_cols[0]:
        status = health_data.get("status", "unknown") if health_data else "error"
        status_class = "status-healthy" if status == "healthy" else "status-error"
        st.markdown(
            f'<div class="status-indicator {status_class}"></div>**System Status:** {status.title()}',
            unsafe_allow_html=True,
        )

    with health_cols[1]:
        db_status = (
            health_data.get("database", {}).get("status", "unknown")
            if health_data
            else "error"
        )
        db_class = "status-healthy" if db_status == "connected" else "status-error"
        st.markdown(
            f'<div class="status-indicator {db_class}"></div>**Database:** {db_status.title()}',
            unsafe_allow_html=True,
        )

    with health_cols[2]:
        vector_status = (
            health_data.get("vector_database", {}).get("status", "unknown")
            if health_data
            else "error"
        )
        vector_class = (
            "status-healthy" if vector_status == "healthy" else "status-error"
        )
        st.markdown(
            f'<div class="status-indicator {vector_class}"></div>**Vector DB:** {vector_status.title()}',
            unsafe_allow_html=True,
        )

    with health_cols[3]:
        openai_status = (
            health_data.get("openai", "not_configured") if health_data else "error"
        )
        openai_class = (
            "status-healthy" if openai_status == "configured" else "status-warning"
        )
        st.markdown(
            f'<div class="status-indicator {openai_class}"></div>**OpenAI:** {openai_status.title()}',
            unsafe_allow_html=True,
        )

    # Key Metrics
    st.subheader("📈 Key Performance Indicators")

    metric_cols = st.columns(6)

    with metric_cols[0]:
        st.metric(
            "Total Queries",
            performance_data["total_queries"],
            delta=f"+{dashboard_data['recent_queries_count']} recent",
        )

    with metric_cols[1]:
        st.metric(
            "Avg Response Time",
            f"{performance_data['avg_response_time']:.2f}s",
            delta=f"{'↑' if performance_data['avg_response_time'] > 2.0 else '↓'} Target: <2s",
        )

    with metric_cols[2]:
        st.metric(
            "Success Rate",
            f"{performance_data['success_rate']*100:.1f}%",
            delta=f"{'↑' if performance_data['success_rate'] > 0.95 else '↓'} Target: >95%",
        )

    with metric_cols[3]:
        st.metric(
            "Quality Score",
            f"{performance_data['avg_quality_score']:.2f}/5",
            delta=f"{'↑' if performance_data['avg_quality_score'] > 3.5 else '↓'} Target: >3.5",
        )

    with metric_cols[4]:
        st.metric(
            "User Satisfaction",
            f"{performance_data['user_satisfaction']:.2f}/5",
            delta=f"{dashboard_data['recent_feedback_count']} feedback",
        )

    with metric_cols[5]:
        st.metric(
            "Error Count",
            dashboard_data["error_count"],
            delta=f"{'🔴' if dashboard_data['error_count'] > 0 else '🟢'} Errors",
        )

    # Charts Section
    st.subheader("📊 Performance Analytics")

    # Create charts
    perf_charts = create_performance_charts(dashboard_data)
    monitoring_charts = create_monitoring_charts(performance_data)

    # Display charts in tabs
    chart_tabs = st.tabs(
        ["📊 Overview", "📈 Performance", "🔍 Monitoring", "📋 Data Tables"]
    )

    with chart_tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(perf_charts["kpi_chart"], use_container_width=True)
        with col2:
            st.plotly_chart(perf_charts["feedback_chart"], use_container_width=True)

        st.plotly_chart(perf_charts["volume_chart"], use_container_width=True)

    with chart_tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                monitoring_charts["response_time_dist"], use_container_width=True
            )
        with col2:
            st.plotly_chart(
                monitoring_charts["system_health_gauge"], use_container_width=True
            )

    with chart_tabs[2]:
        st.subheader("🔍 System Monitoring")

        # Recent Activity
        st.markdown("### Recent System Activity")
        activity_data = {
            "Timestamp": [datetime.now() - timedelta(minutes=i * 5) for i in range(10)],
            "Event": [
                "Query processed",
                "Document uploaded",
                "User login",
                "Feedback received",
            ]
            * 3,
            "Status": ["Success", "Success", "Success", "Success"] * 3,
            "Duration": [f"{1.2 + i*0.1:.1f}s" for i in range(10)],
        }

        activity_df = pd.DataFrame(activity_data[:10])  # Take first 10 rows
        st.dataframe(activity_df, use_container_width=True)

        # Alerts and Warnings
        st.markdown("### 🚨 Alerts & Warnings")
        if dashboard_data["error_count"] > 0:
            st.warning(
                f"⚠️ {dashboard_data['error_count']} errors detected in the last {selected_range.lower()}"
            )

        if performance_data["avg_response_time"] > 2.0:
            st.warning(
                f"⚠️ Response time ({performance_data['avg_response_time']:.2f}s) exceeds target (<2s)"
            )

        if performance_data["success_rate"] < 0.95:
            st.error(
                f"🔴 Success rate ({performance_data['success_rate']*100:.1f}%) below target (95%)"
            )

        if not any(
            [
                dashboard_data["error_count"] > 0,
                performance_data["avg_response_time"] > 2.0,
                performance_data["success_rate"] < 0.95,
            ]
        ):
            st.success("✅ All systems operating normally")

    with chart_tabs[3]:
        st.subheader("📋 Raw Data")

        # Performance Data Table
        st.markdown("### Performance Metrics")
        perf_df = pd.DataFrame([performance_data])
        st.dataframe(perf_df, use_container_width=True)

        # Query Volume Data
        st.markdown("### Query Volume by Day")
        volume_df = pd.DataFrame(
            {
                "Date": list(dashboard_data["query_volume_by_day"].keys()),
                "Query Count": list(dashboard_data["query_volume_by_day"].values()),
            }
        )
        st.dataframe(volume_df, use_container_width=True)

        # Feedback Distribution
        st.markdown("### Feedback Distribution")
        feedback_df = pd.DataFrame(
            {
                "Rating": [
                    f"{k} Stars" for k in dashboard_data["feedback_distribution"].keys()
                ],
                "Count": list(dashboard_data["feedback_distribution"].values()),
            }
        )
        st.dataframe(feedback_df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(
        f"**Dashboard Version:** 1.0 | **API Endpoint:** {API_BASE_URL} | **Data Refresh:** {datetime.now().strftime('%H:%M:%S')}"
    )


if __name__ == "__main__":
    render_dashboard()

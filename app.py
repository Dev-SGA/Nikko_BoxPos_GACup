import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from io import BytesIO
import numpy as np
from PIL import Image
from matplotlib.lines import Line2D

# ==========================
# Page Configuration
# ==========================
st.set_page_config(layout="wide", page_title="Box Positioning Map")

st.title("Box Positioning Map")
st.caption("Click on a dot on the pitch to inspect the event.")

# ==========================
# Box Positioning Data
# ==========================
box_positioning_matches_data = {
    "Vs San Jose": [
        (99.06, 49.81, "videos/1 - SJ"),
        (98.40, 54.46, "videos/4 - SJ"),
        (99.56, 26.70, "videos/5 - SJ"),
        (110.54, 36.51, "videos/3 - SJ"),
        (104.38, 52.30, "videos/2 - SJ"),
    ],
    "Vs Copehagen": [
        (93.25, 28.86, "videos/3 - CP"),
        (110.87, 42.16, "videos/1 -CP"),
        (103.72, 55.46, "videos/2 - CP"),
    ],
    "Vs Sporting": [
        (96.41, 49.48, "videos/1 - SP.mp4"),
    ],
}

# ==========================
# Create DataFrames
# ==========================
dfs_by_match = {}
for match_name, events in box_positioning_matches_data.items():
    df_match = pd.DataFrame(events, columns=["x", "y", "video"])
    df_match["number"] = np.arange(1, len(df_match) + 1)
    dfs_by_match[match_name] = df_match

df_all = pd.concat(dfs_by_match.values(), ignore_index=True)
full_data = {"All Games": df_all}
full_data.update(dfs_by_match)

# ==========================
# Helpers
# ==========================
def has_video_value(v) -> bool:
    return pd.notna(v) and str(v).strip() != ""

# ==========================
# Sidebar
# ==========================
st.sidebar.header("Match Selection")
selected_match = st.sidebar.radio("Select a match", list(full_data.keys()), index=0)

df = full_data[selected_match].copy()

# ==========================
# Layout
# ==========================
col_map, col_video = st.columns(2)

with col_map:
    st.subheader("Box Positioning Map")

    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="#f8f8f8",
        line_color="#4a4a4a"
    )
    fig, ax = pitch.draw(figsize=(8, 5.6))

    pitch.scatter(
        df["x"],
        df["y"],
        ax=ax,
        marker="o",
        s=95,
        color="#2F80ED",
        edgecolors="white",
        linewidths=1.0,
        zorder=3
    )

    ax.annotate(
        "",
        xy=(70, 83),
        xytext=(50, 83),
        arrowprops=dict(arrowstyle="->", color="#4a4a4a", lw=1.5)
    )
    ax.text(
        60, 86,
        "Attack Direction",
        ha="center",
        va="center",
        fontsize=9,
        color="#4a4a4a",
        fontweight="bold"
    )

    legend_elements = [
        Line2D(
            [0], [0],
            marker="o",
            color="w",
            label="Box Positioning",
            markerfacecolor="#2F80ED",
            markeredgecolor="white",
            markersize=9,
            linestyle="None"
        )
    ]

    legend = ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        facecolor="white",
        edgecolor="#333333",
        fontsize="small",
        title="Events",
        title_fontsize="medium",
        labelspacing=1.0,
        borderpad=0.8,
        framealpha=0.95
    )
    legend.get_title().set_fontweight("bold")

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img_obj = Image.open(buf)

    click = streamlit_image_coordinates(img_obj, width=700)
    plt.close(fig)

# ==========================
# Click Interaction
# ==========================
selected_event = None

if click is not None:
    real_w, real_h = img_obj.size
    disp_w, disp_h = click["width"], click["height"]

    pixel_x = click["x"] * (real_w / disp_w)
    pixel_y = click["y"] * (real_h / disp_h)

    mpl_pixel_y = real_h - pixel_y
    coords = ax.transData.inverted().transform((pixel_x, mpl_pixel_y))
    field_x, field_y = coords[0], coords[1]

    df_sel = df.copy()
    df_sel["dist"] = np.sqrt((df_sel["x"] - field_x) ** 2 + (df_sel["y"] - field_y) ** 2)

    RADIUS = 5
    candidates = df_sel[df_sel["dist"] < RADIUS]

    if not candidates.empty:
        selected_event = candidates.loc[candidates["dist"].idxmin()]

# ==========================
# Video / Event Details
# ==========================
with col_video:
    st.subheader("Event Details")

    if selected_event is not None:
        st.success(f"Selected Event: Box Positioning #{int(selected_event['number'])}")
        st.info(f"Position: X: {selected_event['x']:.2f}, Y: {selected_event['y']:.2f}")

        if has_video_value(selected_event["video"]):
            try:
                st.video(selected_event["video"])
            except Exception:
                st.error(f"Video file not found: {selected_event['video']}")
        else:
            st.warning("No video footage is available for this event.")
    else:
        st.info("Select a dot on the pitch to view event details.")


import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "gtfs_dropdown",
    path=os.path.join(os.path.dirname(__file__), "frontend/build")
)

def gtfs_dropdown(options: list[str]):
    return _component_func(options=options, default="")

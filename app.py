import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import json
import os
import csv
import urllib.parse
import streamlit.components.v1 as components

# Define the persistent storage file path
SAVE_FILE = "network_data.json"

# Set up page configuration
st.set_page_config(page_title="Multi-Scenario Network Suite", layout="wide")

st.title("Multi-Scenario Persistent 3D Social Constellation")
st.markdown("""
* **Persistence Status:** Active. Changes are automatically serialized to `network_data.json`.
* **Data Ingestion System:** Active. The ingestion engine standardizes unstructured text input, CSV columns, and JSON arrays into clean node entities.
""")

# --- PERSISTENCE UTILITIES (SAVE/LOAD) ---
def load_persisted_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"Error loading persisted data: {e}")
    return None

def save_persisted_data():
    data_to_save = {"scenarios": {}}
    for sc in ["Scenario Alpha", "Scenario Beta", "Scenario Gamma"]:
        data_to_save["scenarios"][sc] = {
            "people": st.session_state.get(f"people_{sc}", ["Jinan"]),
            "friends": st.session_state.get(f"friends_{sc}", {"Jinan": ""})
        }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        st.sidebar.error(f"Failed to execute auto-save to disk: {e}")

# --- INITIALIZE OR RESTORE MEMORY ---
saved_data = load_persisted_data()
scenarios = ["Scenario Alpha", "Scenario Beta", "Scenario Gamma"]

for sc in scenarios:
    if f"people_{sc}" not in st.session_state:
        if saved_data and sc in saved_data["scenarios"]:
            st.session_state[f"people_{sc}"] = saved_data["scenarios"][sc]["people"]
        else:
            st.session_state[f"people_{sc}"] = ["Jinan"]
            
    if f"friends_{sc}" not in st.session_state:
        if saved_data and sc in saved_data["scenarios"]:
            st.session_state[f"friends_{sc}"] = saved_data["scenarios"][sc]["friends"]
        else:
            st.session_state[f"friends_{sc}"] = {"Jinan": ""}

# --- GLOBAL VISUAL SYSTEM CONFIGURATION ---
st.sidebar.header("Constellation Styling")
color_theme = st.sidebar.selectbox("Color Palette", ["Plasma", "Viridis", "Inferno", "Magma", "Cividis"])
node_size_global = st.sidebar.slider("Node Display Radius", min_value=4, max_value=20, value=10, step=1)
edge_color_global = st.sidebar.color_picker("Link Line Color", value="#888888")

# --- SIDEBAR: SEARCH & PATHFINDING ---
st.sidebar.markdown("---")
with st.sidebar.expander("Search and Pathfinding Utilities", expanded=False):
    search_target_sc = st.selectbox("Select Scenario to Search:", options=scenarios, key="search_target_sc")
    all_active_nodes = sorted(list(st.session_state[f"people_{search_target_sc}"]))
    
    target_pinpoint_global = st.selectbox("Target Node Location Pinpoint:", options=["None"] + all_active_nodes, key="global_pinpoint_select")
    st.markdown("#### Connection Route Finder")
    path_start_global = st.selectbox("Origin Node:", options=all_active_nodes, key="global_path_start")
    path_end_global = st.selectbox("Destination Node:", options=all_active_nodes, key="global_path_end")

# --- MAIN WORKSPACE MULTI-TAB SCENARIOS ---
tabs = st.tabs([sc for sc in scenarios])

for index, tab_object in enumerate(tabs):
    active_sc = scenarios[index]
    
    with tab_object:
        col_entry, col_graph = st.columns([1, 2])
        
        with col_entry:
            st.markdown(f"### {active_sc} Registry")
            
            if st.button(f"Reset and Clear Current Canvas", key=f"clear_{active_sc}", use_container_width=True):
                st.session_state[f"people_{active_sc}"] = ["Jinan"]
                st.session_state[f"friends_{active_sc}"] = {"Jinan": ""}
                save_persisted_data()
                st.rerun()
                
            st.markdown("---")
            
            # --- SCENARIO BETA: DATA INGESTION ENGINE ---
            if active_sc == "Scenario Beta":
                st.markdown("#### Structured Data Ingestion Engine")
                
                import_mode = st.radio("Select Input Method:", ["Raw Clipboard Paste", "File Upload (CSV/JSON/TXT)"], horizontal=True)
                parsed_handles = []

                if import_mode == "Raw Clipboard Paste":
                    bulk_input = st.text_area("Paste unstructured text or platform data strings here:", height=120, key="global_bulk_import_area")
                    if st.button("Process Clipboard Data", use_container_width=True):
                        raw_tokens = bulk_input.replace("\n", ",").replace(" ", ",").split(",")
                        for token in raw_tokens:
                            clean = token.strip().replace("@", "")
                            if clean.lower() in ["follow", "following", "requested", "remove", "verified", "profile", "posts", "followers", "message"]:
                                continue
                            if clean and all(c.isalnum() or c in "._" for c in clean):
                                if clean not in parsed_handles:
                                    parsed_handles.append(clean)

                else:
                    uploaded_file = st.file_uploader("Upload Data Sheet", type=["csv", "json", "txt"])
                    if uploaded_file is not None:
                        file_contents = uploaded_file.read().decode("utf-8", errors="ignore")
                        
                        if uploaded_file.name.endswith(".json"):
                            try:
                                data_obj = json.loads(file_contents)
                                if isinstance(data_obj, list):
                                    for item in data_obj:
                                        if isinstance(item, str): parsed_handles.append(item.replace("@", "").strip())
                                elif isinstance(data_obj, dict):
                                    for key in ["users", "profiles", "relationships", "followers"]:
                                        if key in data_obj and isinstance(data_obj[key], list):
                                            for entry in data_obj[key]:
                                                if isinstance(entry, str): parsed_handles.append(entry.replace("@", "").strip())
                                                elif isinstance(entry, dict) and "username" in entry: parsed_handles.append(str(entry["username"]))
                            except:
                                st.error("Malformed JSON structure detected.")
                                
                        elif uploaded_file.name.endswith(".csv"):
                            reader = csv.reader(file_contents.splitlines())
                            for row in reader:
                                for cell in row:
                                    clean = cell.strip().replace("@", "")
                                    if clean and not clean.replace(".","").replace("_","").isalnum(): continue
                                    if clean and clean.lower() not in ["username", "handle", "id", "name"]:
                                        parsed_handles.append(clean)
                                        
                        else:
                            for line in file_contents.splitlines():
                                clean = line.strip().replace("@", "")
                                if clean and all(c.isalnum() or c in "._" for c in clean):
                                    parsed_handles.append(clean)

                if st.button("Run Data Aggregation", use_container_width=True) if import_mode == "File Upload (CSV/JSON/TXT)" else False or len(parsed_handles) > 0:
                    if parsed_handles:
                        current_jinan_connections = st.session_state[f"friends_{active_sc}"].get("Jinan", "")
                        existing_list = [f.strip() for f in current_jinan_connections.split(",") if f.strip()]
                        
                        for handle in parsed_handles:
                            if handle not in st.session_state[f"people_{active_sc}"]:
                                st.session_state[f"people_{active_sc}"].append(handle)
                                st.session_state[f"friends_{active_sc}"][handle] = ""
                            if handle not in existing_list and handle != "Jinan":
                                existing_list.append(handle)
                        
                        st.session_state[f"friends_{active_sc}"]["Jinan"] = ", ".join(existing_list)
                        save_persisted_data()
                        st.success(f"Noise filtered successfully. Appended {len(parsed_handles)} profiles.")
                        st.rerun()
                st.markdown("---")

            # --- DYNAMIC RELATIONSHIP BOX GENERATION ---
            current_people = list(st.session_state[f"people_{active_sc}"])
            state_mutated = False

            for person in current_people:
                current_val = st.session_state[f"friends_{active_sc}"].get(person, "")
                box_label = f"Mutual connections of {person}" if active_sc == "Scenario Beta" else f"Connections of {person}"
                
                user_input = st.text_input(f"Link: {box_label}:", value=current_val, key=f"input_{active_sc}_{person}")
                
                if user_input != current_val:
                    st.session_state[f"friends_{active_sc}"][person] = user_input
                    state_mutated = True
                
                with st.expander(f"Bulk Text Importer for {person}", expanded=False):
                    local_bulk_input = st.text_area("Paste copied text list for this individual here:", height=80, key=f"bulk_local_{active_sc}_{person}")
                    if st.button("Process and Link Mutual Connections", key=f"btn_local_{active_sc}_{person}", use_container_width=True):
                        raw_tokens = local_bulk_input.replace("\n", ",").replace(" ", ",").split(",")
                        local_parsed = []
                        for token in raw_tokens:
                            clean = token.strip().replace("@", "")
                            if clean and clean not in local_parsed:
                                local_parsed.append(clean)
                        
                        if local_parsed:
                            existing_list = [f.strip() for f in current_val.split(",") if f.strip()]
                            for handle in local_parsed:
                                if handle not in st.session_state[f"people_{active_sc}"]:
                                    st.session_state[f"people_{active_sc}"].append(handle)
                                    st.session_state[f"friends_{active_sc}"][handle] = ""
                                if handle not in existing_list and handle != person:
                                    existing_list.append(handle)
                            
                            st.session_state[f"friends_{active_sc}"][person] = ", ".join(existing_list)
                            state_mutated = True
                
                friends_list = [f.strip().replace("@", "") for f in st.session_state[f"friends_{active_sc}"][person].split(",") if f.strip()]
                for friend in friends_list:
                    if friend not in st.session_state[f"people_{active_sc}"]:
                        st.session_state[f"people_{active_sc}"].append(friend)
                        st.session_state[f"friends_{active_sc}"][friend] = ""
                        state_mutated = True

            if state_mutated:
                save_persisted_data()
                st.rerun()

            # --- AUTO-PRUNING ENGINE ---
            temp_G = nx.Graph()
            for p in st.session_state[f"people_{active_sc}"]: temp_G.add_node(p)
            for person, friends_str in st.session_state[f"friends_{active_sc}"].items():
                flist = [f.strip().replace("@", "") for f in friends_str.split(",") if f.strip()]
                for friend in flist:
                    if temp_G.has_node(person) and temp_G.has_node(friend): temp_G.add_edge(person, friend)

            nodes_to_auto_prune = [n for n in list(temp_G.nodes()) if n != "Jinan" and temp_G.degree(n) == 0]
            if nodes_to_auto_prune:
                for target in nodes_to_auto_prune:
                    if target in st.session_state[f"people_{active_sc}"]: st.session_state[f"people_{active_sc}"].remove(target)
                    if target in st.session_state[f"friends_{active_sc}"]: del st.session_state[f"friends_{active_sc}"][target]
                save_persisted_data()
                st.rerun()

        with col_graph:
            # --- GRAPH CONSTRUCT ENGINE ---
            G_active = nx.Graph()
            for person in st.session_state[f"people_{active_sc}"]: G_active.add_node(person)
            for person, friends_string in st.session_state[f"friends_{active_sc}"].items():
                friends_list = [f.strip().replace("@", "") for f in friends_string.split(",") if f.strip()]
                for friend in friends_list:
                    if G_active.has_node(person) and G_active.has_node(friend): G_active.add_edge(person, friend)

            if len(G_active.nodes()) > 0:
                pos_active = nx.fruchterman_reingold_layout(G_active, dim=3, seed=42)
            else:
                pos_active = {}

            # --- PATHFINDING TRACE LOGIC ---
            shortest_path_nodes = []
            shortest_path_edges = set()
            if active_sc == search_target_sc and path_start_global and path_end_global and path_start_global != path_end_global:
                try:
                    shortest_path_nodes = nx.shortest_path(G_active, source=path_start_global, target=path_end_global)
                    for i in range(len(shortest_path_nodes) - 1):
                        shortest_path_edges.add((shortest_path_nodes[i], shortest_path_nodes[i+1]))
                        shortest_path_edges.add((shortest_path_nodes[i+1], shortest_path_nodes[i]))
                    st.success("Route Found: " + " -> ".join([f"{n}" for n in shortest_path_nodes]))
                except nx.NetworkXNoPath:
                    st.error("No path connects these nodes.")

            # Metrics Display
            sm1, sm2, sm3 = st.columns(3)
            sm1.metric("Total Profile Nodes" if active_sc == "Scenario Beta" else "Active Nodes", len(G_active.nodes()))
            sm2.metric("Total Link Connections", len(G_active.edges()))
            sm3.metric("Isolated Social Islands", nx.number_connected_components(G_active))

            # --- PLOTLY 3D GRAPH ASSEMBLY ---
            data_traces = []
            edge_x, edge_y, edge_z = [], [], []
            path_edge_x, path_edge_y, path_edge_z = [], [], []
            
            for u, v in G_active.edges():
                x0, y0, z0 = pos_active[u]
                x1, y1, z1 = pos_active[v]
                if (u, v) in shortest_path_edges:
                    path_edge_x.extend([x0, x1, None])
                    path_edge_y.extend([y0, y1, None])
                    path_edge_z.extend([z0, z1, None])
                else:
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_z.extend([z0, z1, None])

            if edge_x: data_traces.append(go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, line=dict(width=2, color=edge_color_global), hoverinfo='none', mode='lines'))
            if path_edge_x: data_traces.append(go.Scatter3d(x=path_edge_x, y=path_edge_y, z=path_edge_z, line=dict(width=6, color="#FF3333"), mode='lines'))

            node_x, node_y, node_z, node_text, node_colors, custom_sizes, border_colors = [], [], [], [], [], [], []
            
            for node in G_active.nodes():
                x, y, z = pos_active[node]
                node_x.append(x)
                node_y.append(y)
                node_z.append(z)
                deg = G_active.degree(node)
                node_colors.append(deg)
                
                if active_sc == "Scenario Beta" and node != "Jinan":
                    node_text.append(f"<b>Handle:</b> {node}<br><b>Connections:</b> {deg}<br><i>Expand cross-references below</i>")
                else:
                    node_text.append(f"<b>Identity:</b> {node}<br><b>Connections:</b> {deg}")
                
                if active_sc == search_target_sc and node == target_pinpoint_global:
                    custom_sizes.append(node_size_global * 2.2)
                    border_colors.append("#00FFFF")
                elif active_sc == search_target_sc and node in shortest_path_nodes:
                    custom_sizes.append(node_size_global * 1.5)
                    border_colors.append("#FF3333")
                else:
                    custom_sizes.append(node_size_global)
                    border_colors.append("#FFFFFF")

            if node_x:
                node_trace = go.Scatter3d(
                    x=node_x, y=node_y, z=node_z, mode='markers', hovertext=node_text, hoverinfo='text',
                    marker=dict(showscale=True, colorscale=color_theme, color=node_colors, size=custom_sizes, line=dict(width=1.5, color=border_colors))
                )
                data_traces.append(node_trace)

            layout_active = go.Layout(
                height=760, showlegend=False,
                scene=dict(
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
                ),
                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
                margin=dict(l=0, r=0, b=0, t=0), hovermode='closest'
            )
            
            fig_active = go.Figure(data=data_traces, layout=layout_active)
            
            # --- CONVERT GRAPH TO HTML STRING WITH CONTROLS ---
            fig_json = fig_active.to_json()
            unique_id_tag = f"plot_{active_sc.replace(' ', '_')}"
            
            sandbox_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
                <style>
                    body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background-color: #0E1117; font-family: system-ui, sans-serif; }}
                    #render_box {{ width: 100%; height: 100%; position: relative; }}
                    
                    #hud_panel {{
                        position: absolute;
                        bottom: 25px;
                        left: 25px;
                        z-index: 9999;
                        display: flex;
                        gap: 10px;
                    }}
                    
                    .hud_btn {{
                        background: rgba(38, 41, 50, 0.9);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        padding: 10px 16px;
                        border-radius: 8px;
                        color: white;
                        cursor: pointer;
                        font-size: 13px;
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                        transition: all 0.2s ease;
                        user-select: none;
                    }}
                    
                    .hud_btn:hover {{
                        background: rgba(255, 255, 255, 0.15);
                        border-color: rgba(255, 255, 255, 0.3);
                    }}
                    
                    :-webkit-full-screen #render_box {{ height: 100vh; }}
                    :-moz-full-screen #render_box {{ height: 100vh; }}
                    :fullscreen #render_box {{ height: 100vh; }}
                </style>
            </head>
            <body>
                <div id="render_box">
                    <div id="hud_panel">
                        <div id="control_orbit_btn" class="hud_btn" onclick="toggleOrbit()">Pause Auto-Orbit</div>
                        <div id="control_fs_btn" class="hud_btn" onclick="toggleFullscreen()">View Fullscreen</div>
                    </div>
                    <div id="{unique_id_tag}" style="width: 100%; height: 100%;"></div>
                </div>
                
                <script>
                    const plotData = {fig_json};
                    const chartDomNode = document.getElementById('{unique_id_tag}');
                    const orbitBtn = document.getElementById('control_orbit_btn');
                    const containerBox = document.getElementById('render_box');
                    
                    Plotly.newPlot(chartDomNode, plotData.data, plotData.layout, {{responsive: true, displayModeBar: true}});
                    
                    let radAngle = 0;
                    const radius = 1.7; 
                    let isOrbiting = true;

                    function toggleOrbit() {{
                        isOrbiting = !isOrbiting;
                        if(isOrbiting) {{
                            orbitBtn.innerHTML = "Pause Auto-Orbit";
                            orbitBtn.style.color = "white";
                            try {{
                                const currentEye = chartDomNode._fullLayout.scene.camera.eye;
                                radAngle = Math.atan2(currentEye.y, currentEye.x);
                            }} catch(e) {{}}
                        }} else {{
                            orbitBtn.innerHTML = "Resume Auto-Orbit (Manual Mode Active)";
                            orbitBtn.style.color = "#00FFFF";
                        }}
                    }}
                    
                    function toggleFullscreen() {{
                        if (!document.fullscreenElement) {{
                            containerBox.requestFullscreen().catch(err => {{
                                alert(`Error enabling full-screen: ${{err.message}}`);
                            }});
                        }} else {{
                            document.exitFullscreen();
                        }}
                    }}
                    
                    document.addEventListener('fullscreenchange', () => {{
                        Plotly.Plots.resize(chartDomNode);
                    }});

                    function runCameraOrbitLoop() {{
                        if (isOrbiting) {{
                            radAngle += 0.003; 
                            const nextX = radius * Math.cos(radAngle);
                            const nextY = radius * Math.sin(radAngle);
                            
                            try {{
                                Plotly.relayout(chartDomNode, {{
                                    'scene.camera.eye': {{ x: nextX, y: nextY, z: 1.0 }}
                                }});
                            }} catch(err) {{}}
                        }}
                        requestAnimationFrame(runCameraOrbitLoop);
                    }}
                    
                    setTimeout(runCameraOrbitLoop, 300);
                </script>
            </body>
            </html>
            """
            
            components.html(sandbox_html, height=770)
            
            # --- DIGITAL IDENTITY CROSS-REFERENCE EXPANDERS ---
            if active_sc == "Scenario Beta" and len(G_active.nodes()) > 1:
                st.markdown("### Profile Reference Dashboard")
                
                dash_col1, dash_col2 = st.columns(2)
                sorted_profiles = sorted([n for n in G_active.nodes() if n != "Jinan"])
                
                for idx, n in enumerate(sorted_profiles):
                    target_column = dash_col1 if idx % 2 == 0 else dash_col2
                    
                    with target_column:
                        with st.expander(f"Profile: {n}", expanded=False):
                            encoded_handle = urllib.parse.quote(n)
                            st.markdown(f"**Target Identifier Reference:** `{n}`")
                            
                            btn_ig, btn_li, btn_web = st.columns(3)
                            with btn_ig:
                                st.link_button("Instagram", f"https://www.instagram.com/{encoded_handle}", use_container_width=True)
                            with btn_li:
                                linkedin_search_url = f"https://www.linkedin.com/search/results/all/?keywords={encoded_handle}"
                                st.link_button("LinkedIn Match", linkedin_search_url, use_container_width=True)
                            with btn_web:
                                web_recon_url = f"https://www.google.com/search?q=%22{encoded_handle}%22+site:linkedin.com+OR+site:instagram.com"
                                st.link_button("Web Footprints", web_recon_url, use_container_width=True)
                                
                            st.caption("Verify if cross-platform profiles correlate regarding bio data structural text or location markers.")

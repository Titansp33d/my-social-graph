import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import json
import os
import urllib.parse
import streamlit.components.v1 as components

# Define the persistent storage file path
SAVE_FILE = "network_data.json"

# Set up page configuration
st.set_page_config(page_title="Multi-Scenario Network Suite", layout="wide")

st.title("🛰️ Multi-Scenario Persistent 3D Social Constellation")
st.markdown("""
* **Persistence Active:** Changes are automatically saved to `network_data.json`.
* **Automated View Angle:** The web browser will attempt to rotate the viewport camera around the static 3D layout smoothly.
""")

# --- PERSISTENCE UTILITIES (SAVE/LOAD) ---
def load_persisted_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.sidebar.error(f"Error loading saved data: {e}")
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
        st.sidebar.error(f"Failed to auto-save to disk: {e}")

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
st.sidebar.header("🎨 Constellation Styling")
color_theme = st.sidebar.selectbox("Color Palette", ["Plasma", "Viridis", "Inferno", "Magma", "Cividis"])
node_size_global = st.sidebar.slider("Node Display Radius", min_value=4, max_value=20, value=10, step=1)
edge_color_global = st.sidebar.color_picker("Link Line Color", value="#888888")

# --- SIDEBAR: SEARCH & PATHFINDING ---
st.sidebar.markdown("---")
with st.sidebar.expander("🔍 Search & Pathfinding Tools", expanded=False):
    search_target_sc = st.selectbox("Select Scenario to Search:", options=scenarios, key="search_target_sc")
    all_active_nodes = sorted(list(st.session_state[f"people_{search_target_sc}"]))
    
    target_pinpoint_global = st.selectbox("🎯 Pinpoint Node Location:", options=["None"] + all_active_nodes, key="global_pinpoint_select")
    st.markdown("#### 🛣️ Friendship Route Finder")
    path_start_global = st.selectbox("Start Person:", options=all_active_nodes, key="global_path_start")
    path_end_global = st.selectbox("End Person:", options=all_active_nodes, key="global_path_end")

# --- MAIN WORKSPACE MULTI-TAB SCENARIOS ---
tabs = st.tabs([f"👥 {sc}" for sc in scenarios])

for index, tab_object in enumerate(tabs):
    active_sc = scenarios[index]
    
    with tab_object:
        col_entry, col_graph = st.columns([1, 2])
        
        with col_entry:
            st.markdown(f"### {active_sc} Registry")
            
            if st.button(f"Reset & Clear This Canvas", key=f"clear_{active_sc}", use_container_width=True):
                st.session_state[f"people_{active_sc}"] = ["Jinan"]
                st.session_state[f"friends_{active_sc}"] = {"Jinan": ""}
                save_persisted_data()
                st.rerun()
                
            st.markdown("---")
            
            # --- SCENARIO BETA: GLOBAL BASE BULK IMPORT ENGINE ---
            if active_sc == "Scenario Beta":
                st.markdown("#### 🚀 Global Instagram Importer (Add your main followers)")
                bulk_input = st.text_area("Paste raw text list here:", height=90, key="global_bulk_import_area")
                
                if st.button("Automate Main Population", use_container_width=True):
                    raw_tokens = bulk_input.replace("\n", ",").replace(" ", ",").split(",")
                    parsed_handles = []
                    for token in raw_tokens:
                        clean = token.strip().replace("@", "")
                        if clean and clean not in parsed_handles:
                            parsed_handles.append(clean)
                    
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
                        st.success(f"Successfully processed and mapped {len(parsed_handles)} profiles!")
                        st.rerun()
                st.markdown("---")

            # --- DYNAMIC RELATIONSHIP BOX GENERATION + LOCAL MINI BULK IMPORTERS ---
            current_people = list(st.session_state[f"people_{active_sc}"])
            state_mutated = False

            for person in current_people:
                current_val = st.session_state[f"friends_{active_sc}"].get(person, "")
                box_label = f"Mutual connections of @{person}" if active_sc == "Scenario Beta" else f"Friends of {person}"
                
                user_input = st.text_input(f"🔗 {box_label}:", value=current_val, key=f"input_{active_sc}_{person}")
                
                if user_input != current_val:
                    st.session_state[f"friends_{active_sc}"][person] = user_input
                    state_mutated = True
                
                with st.expander(f"📋 Bulk Text Importer for {person}", expanded=False):
                    local_bulk_input = st.text_area("Paste copied text list for this individual here:", height=80, key=f"bulk_local_{active_sc}_{person}")
                    if st.button("Process & Link Mutuals", key=f"btn_local_{active_sc}_{person}", use_container_width=True):
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
                    st.success(f"⛓️ **Route Found:** " + " ➔ ".join([f"**@{n}**" if active_sc == "Scenario Beta" else f"**{n}**" for n in shortest_path_nodes]))
                except nx.NetworkXNoPath:
                    st.error("❌ No path connects these nodes.")

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
                    node_text.append(f"<b>IG Handle:</b> @{node}<br><b>Connections:</b> {deg}<br>🔗 <i>Expand cross-references below</i>")
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
                height=800, showlegend=False,
                scene=dict(
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
                ),
                margin=dict(l=0, r=0, b=0, t=0), hovermode='closest'
            )
            
            fig_active = go.Figure(data=data_traces, layout=layout_active)
            
            chart_id = f"plotly_canvas_{active_sc.replace(' ', '_')}"
            st.plotly_chart(fig_active, use_container_width=True, key=chart_id)
            
            # --- PERSISTENT BROWSER-SIDE CAMERA ROTATION ENGINE ---
            components.html(
                f"""
                <script>
                const doc = window.parent.document;
                
                function initCameraOrbit() {{
                    const chartWrapper = doc.querySelector('[data-testid="stPlotlyChart"]');
                    if (!chartWrapper) {{
                        setTimeout(initCameraOrbit, 300);
                        return;
                    }}
                    
                    const targetPlot = chartWrapper.querySelector('.js-plotly-plot');
                    if (!targetPlot) {{
                        setTimeout(initCameraOrbit, 300);
                        return;
                    }}

                    let radAngle = 0;
                    const radius = 1.7;
                    
                    function stepOrbit() {{
                        radAngle += 0.002; 
                        const newX = radius * Math.cos(radAngle);
                        const newY = radius * Math.sin(radAngle);
                        
                        try {{
                            window.parent.Plotly.relayout(targetPlot, {{
                                'scene.camera.eye': {{ x: newX, y: newY, z: 1.0 }}
                            }});
                        }} catch(err) {{
                            // Fail silently if chart is redrawing
                        }}
                        requestAnimationFrame(stepOrbit);
                    }}
                    stepOrbit();
                }}
                setTimeout(initCameraOrbit, 500);
                </script>
                """,
                height=0
            )
            
            # --- DIGITAL IDENTITY CROSS-REFERENCE EXPANDERS ---
            if active_sc == "Scenario Beta" and len(G_active.nodes()) > 1:
                st.markdown("### 🔍 Profile Reconnaissance Dashboard")
                
                dash_col1, dash_col2 = st.columns(2)
                sorted_profiles = sorted([n for n in G_active.nodes() if n != "Jinan"])
                
                for idx, n in enumerate(sorted_profiles):
                    target_column = dash_col1 if idx % 2 == 0 else dash_col2
                    
                    with target_column:
                        with st.expander(f"👤 @{n} (Verify Platform Footprint)", expanded=False):
                            encoded_handle = urllib.parse.quote(n)
                            st.markdown(f"**Target Handle Reference:** `{n}`")
                            
                            btn_ig, btn_li, btn_web = st.columns(3)
                            with btn_ig:
                                st.link_button("📸 Instagram", f"https://www.instagram.com/{encoded_handle}", use_container_width=True)
                            with btn_li:
                                linkedin_search_url = f"https://www.linkedin.com/search/results/all/?keywords={encoded_handle}"
                                st.link_button("💼 LinkedIn Match", linkedin_search_url, use_container_width=True)
                            with btn_web:
                                web_recon_url = f"https://www.google.com/search?q=%22{encoded_handle}%22+site:linkedin.com+OR+site:instagram.com"
                                st.link_button("🌐 Web Footprints", web_recon_url, use_container_width=True)
                                
                            st.caption("💡 *Tip: Check if the LinkedIn profile matches the structural bio text or location details seen on their Instagram.*")

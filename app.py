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

st.title("Multi-Scenario Persistent 3D Social Constellation")
st.markdown("""
* **Persistence Status:** Active. Changes are automatically serialized to `network_data.json`.
* **Scalable Profile Manager:** Select individual profiles to edit without DOM/memory limits.
* **Bi-Directional Auto-Sync:** Updating A's followers updates B's following, and vice versa.
* **Cosmic Orbit Layout:** Mutual connections form central core clusters; non-mutual nodes float on the periphery as scattered background stars until reciprocated.
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
            "followers": st.session_state.get(f"followers_{sc}", {"Jinan": ""}),
            "following": st.session_state.get(f"following_{sc}", {"Jinan": ""})
        }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        st.sidebar.error(f"Failed to execute auto-save to disk: {e}")

def cleanup_synthetic_nodes():
    """Purges all generated synthetic nodes ('User_*') from memory and storage."""
    for sc in ["Scenario Alpha", "Scenario Beta", "Scenario Gamma"]:
        peop = st.session_state.get(f"people_{sc}", [])
        st.session_state[f"people_{sc}"] = [p for p in peop if not p.startswith("User_")]
        
        followers = st.session_state.get(f"followers_{sc}", {})
        st.session_state[f"followers_{sc}"] = {
            k: ", ".join([f.strip() for f in v.split(",") if f.strip() and not f.strip().startswith("User_")])
            for k, v in followers.items() if not k.startswith("User_")
        }

        following = st.session_state.get(f"following_{sc}", {})
        st.session_state[f"following_{sc}"] = {
            k: ", ".join([f.strip() for f in v.split(",") if f.strip() and not f.strip().startswith("User_")])
            for k, v in following.items() if not k.startswith("User_")
        }
    save_persisted_data()

# --- INITIALIZE OR RESTORE MEMORY ---
saved_data = load_persisted_data()
scenarios = ["Scenario Alpha", "Scenario Beta", "Scenario Gamma"]

for sc in scenarios:
    if f"people_{sc}" not in st.session_state:
        if saved_data and sc in saved_data["scenarios"]:
            st.session_state[f"people_{sc}"] = saved_data["scenarios"][sc]["people"]
        else:
            st.session_state[f"people_{sc}"] = ["Jinan"]
            
    if f"followers_{sc}" not in st.session_state:
        if saved_data and sc in saved_data["scenarios"]:
            st.session_state[f"followers_{sc}"] = saved_data["scenarios"][sc].get("followers", {"Jinan": ""})
        else:
            st.session_state[f"followers_{sc}"] = {"Jinan": ""}

    if f"following_{sc}" not in st.session_state:
        if saved_data and sc in saved_data["scenarios"]:
            st.session_state[f"following_{sc}"] = saved_data["scenarios"][sc].get("following", {"Jinan": ""})
        else:
            st.session_state[f"following_{sc}"] = {"Jinan": ""}

# --- GLOBAL VISUAL SYSTEM CONFIGURATION ---
st.sidebar.header("Constellation Styling")
color_theme = st.sidebar.selectbox("Color Palette", ["Plasma", "Viridis", "Inferno", "Magma", "Cividis"])
node_size_global = st.sidebar.slider("Node Base Radius", min_value=4, max_value=20, value=10, step=1)
edge_color_global = st.sidebar.color_picker("Link Line Color", value="#888888")

# --- SYNTHETIC / MOCK DATA GENERATOR ---
st.sidebar.markdown("---")
enable_generator = st.sidebar.toggle(
    "Enable Synthetic Generator", 
    value=False, 
    key="toggle_synth_gen",
    on_change=lambda: cleanup_synthetic_nodes() if not st.session_state.toggle_synth_gen else None
)

if enable_generator:
    with st.sidebar.expander("🎲 Synthetic Network Generator", expanded=True):
        target_sc_gen = st.selectbox("Target Scenario:", scenarios, key="opt2_sc_target")
        generator_type = st.selectbox(
            "Network Topology:", 
            ["Scale-Free (Social Hubs)", "Small-World (Clusters)", "Random Mesh"],
            key="opt2_topo_type"
        )
        num_nodes = st.slider("Node Count:", min_value=5, max_value=50, value=15, key="opt2_node_cnt")
        
        col_gen, col_clr = st.columns(2)
        if col_gen.button("Generate", use_container_width=True, key="opt2_gen_btn"):
            if generator_type == "Scale-Free (Social Hubs)":
                m = min(2, num_nodes - 1)
                synth_G = nx.barabasi_albert_graph(num_nodes, m, seed=42)
            elif generator_type == "Small-World (Clusters)":
                synth_G = nx.watts_strogatz_graph(num_nodes, k=min(4, num_nodes - 1), p=0.3, seed=42)
            else:
                synth_G = nx.erdos_renyi_graph(num_nodes, p=0.2, seed=42)

            node_names = [f"User_{i+1}" for i in range(num_nodes)]
            
            existing_people = [p for p in st.session_state[f"people_{target_sc_gen}"] if not p.startswith("User_")]
            st.session_state[f"people_{target_sc_gen}"] = existing_people + node_names
            
            followers_dict = st.session_state[f"followers_{target_sc_gen}"]
            following_dict = st.session_state[f"following_{target_sc_gen}"]

            for u, v in synth_G.edges():
                u_name, v_name = node_names[u], node_names[v]
                
                u_foll = [f.strip() for f in followers_dict.get(u_name, "").split(",") if f.strip()]
                if v_name not in u_foll: u_foll.append(v_name)
                followers_dict[u_name] = ", ".join(u_foll)

                u_ing = [f.strip() for f in following_dict.get(u_name, "").split(",") if f.strip()]
                if v_name not in u_ing: u_ing.append(v_name)
                following_dict[u_name] = ", ".join(u_ing)

                v_foll = [f.strip() for f in followers_dict.get(v_name, "").split(",") if f.strip()]
                if u_name not in v_foll: v_foll.append(u_name)
                followers_dict[v_name] = ", ".join(v_foll)

                v_ing = [f.strip() for f in following_dict.get(v_name, "").split(",") if f.strip()]
                if u_name not in v_ing: v_ing.append(u_name)
                following_dict[v_name] = ", ".join(v_ing)

            st.session_state[f"followers_{target_sc_gen}"] = followers_dict
            st.session_state[f"following_{target_sc_gen}"] = following_dict
            save_persisted_data()
            st.success(f"Generated {num_nodes}-node synthetic network!")
            st.rerun()

        if col_clr.button("Clear Synthetic", use_container_width=True, key="opt2_clr_btn"):
            cleanup_synthetic_nodes()
            st.success("Cleared synthetic nodes!")
            st.rerun()

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
                st.session_state[f"followers_{active_sc}"] = {"Jinan": ""}
                st.session_state[f"following_{active_sc}"] = {"Jinan": ""}
                save_persisted_data()
                st.rerun()
                
            st.markdown("---")
            
            # --- SURVEY INTAKE FORM ---
            with st.expander("📋 Community Connection Survey Form", expanded=False):
                st.markdown("#### Submit Your Network Node")
                
                with st.form(key=f"opt4_survey_form_{active_sc}"):
                    user_name = st.text_input("Your Name / Handle:", placeholder="e.g. Alex").strip()
                    knows_input = st.text_input("People in this network you interact with:", placeholder="e.g. Jinan, Sam, Jordan")
                    connection_type = st.selectbox("Interaction Level:", ["Frequent Collaborator", "Casual Contact", "Project Member"])
                    
                    submit_button = st.form_submit_button("Submit Node Data", use_container_width=True)
                    
                    if submit_button and user_name:
                        user_clean = user_name.replace("@", "")
                        
                        if user_clean not in st.session_state[f"people_{active_sc}"]:
                            st.session_state[f"people_{active_sc}"].append(user_clean)
                        
                        known_list = [k.strip().replace("@", "") for k in knows_input.split(",") if k.strip()]
                        
                        st.session_state[f"followers_{active_sc}"][user_clean] = ", ".join(known_list)
                        st.session_state[f"following_{active_sc}"][user_clean] = ", ".join(known_list)
                        
                        for person in known_list:
                            if person not in st.session_state[f"people_{active_sc}"]:
                                st.session_state[f"people_{active_sc}"].append(person)
                            
                            p_foll = [f.strip() for f in st.session_state[f"followers_{active_sc}"].get(person, "").split(",") if f.strip()]
                            if user_clean not in p_foll: p_foll.append(user_clean)
                            st.session_state[f"followers_{active_sc}"][person] = ", ".join(p_foll)

                            p_ing = [f.strip() for f in st.session_state[f"following_{active_sc}"].get(person, "").split(",") if f.strip()]
                            if user_clean not in p_ing: p_ing.append(user_clean)
                            st.session_state[f"following_{active_sc}"][person] = ", ".join(p_ing)

                        save_persisted_data()
                        st.success(f"Added {user_clean}'s connections to {active_sc}!")
                        st.rerun()

            st.markdown("---")

            # --- SINGLE PROFILE SELECTOR & PERSISTENT WIDGET EDITOR ---
            active_people = sorted(list(st.session_state[f"people_{active_sc}"]))
            
            st.markdown("#### Manage Node Relationships")
            selected_person = st.selectbox(
                "Select Node Profile to Edit:",
                options=active_people,
                key=f"select_profile_{active_sc}"
            )

            if selected_person:
                foll_key = f"area_foll_{active_sc}_{selected_person}"
                ing_key = f"area_ing_{active_sc}_{selected_person}"

                if foll_key not in st.session_state:
                    st.session_state[foll_key] = st.session_state[f"followers_{active_sc}"].get(selected_person, "")
                if ing_key not in st.session_state:
                    st.session_state[ing_key] = st.session_state[f"following_{active_sc}"].get(selected_person, "")

                col_foll, col_ing = st.columns(2)

                with col_foll:
                    input_followers = st.text_area(
                        f"Followers of {selected_person}:", 
                        height=220, 
                        key=foll_key
                    )
                    if st.button("Update Followers", key=f"btn_foll_{active_sc}_{selected_person}", use_container_width=True):
                        raw_tokens = input_followers.replace("\n", ",").replace(" ", ",").split(",")
                        parsed = [t.strip().replace("@", "") for t in raw_tokens if t.strip() and all(c.isalnum() or c in "._-" for c in t.strip())]
                        
                        existing = []
                        for follower_person in parsed:
                            if follower_person not in st.session_state[f"people_{active_sc}"]:
                                st.session_state[f"people_{active_sc}"].append(follower_person)
                            if follower_person not in existing and follower_person != selected_person:
                                existing.append(follower_person)
                            
                            # SYNC: If B is in A's FOLLOWERS -> Add A to B's FOLLOWING list
                            b_following = [f.strip() for f in st.session_state[f"following_{active_sc}"].get(follower_person, "").split(",") if f.strip()]
                            if selected_person not in b_following:
                                b_following.append(selected_person)
                                st.session_state[f"following_{active_sc}"][follower_person] = ", ".join(b_following)

                        st.session_state[f"followers_{active_sc}"][selected_person] = ", ".join(existing)
                        save_persisted_data()
                        st.rerun()

                with col_ing:
                    input_following = st.text_area(
                        f"{selected_person} is Following:", 
                        height=220, 
                        key=ing_key
                    )
                    if st.button("Update Following", key=f"btn_ing_{active_sc}_{selected_person}", use_container_width=True):
                        raw_tokens = input_following.replace("\n", ",").replace(" ", ",").split(",")
                        parsed = [t.strip().replace("@", "") for t in raw_tokens if t.strip() and all(c.isalnum() or c in "._-" for c in t.strip())]
                        
                        existing = []
                        for followed_person in parsed:
                            if followed_person not in st.session_state[f"people_{active_sc}"]:
                                st.session_state[f"people_{active_sc}"].append(followed_person)
                            if followed_person not in existing and followed_person != selected_person:
                                existing.append(followed_person)
                            
                            # INVERSE SYNC: If A is FOLLOWING B -> Add A to B's FOLLOWERS list
                            b_followers = [f.strip() for f in st.session_state[f"followers_{active_sc}"].get(followed_person, "").split(",") if f.strip()]
                            if selected_person not in b_followers:
                                b_followers.append(selected_person)
                                st.session_state[f"followers_{active_sc}"][followed_person] = ", ".join(b_followers)

                        st.session_state[f"following_{active_sc}"][selected_person] = ", ".join(existing)
                        save_persisted_data()
                        st.rerun()

        with col_graph:
            # --- GRAPH CONSTRUCT ENGINE (MUTUAL LINKS + SCATTERED BACKGROUND STARS) ---
            G_directed = nx.DiGraph()
            
            # 1. Register ALL nodes into directed graph
            for person in st.session_state[f"people_{active_sc}"]: 
                G_directed.add_node(person)
            
            for person in st.session_state[f"people_{active_sc}"]:
                foll_list = [f.strip() for f in st.session_state[f"followers_{active_sc}"].get(person, "").split(",") if f.strip()]
                ing_list = [f.strip() for f in st.session_state[f"following_{active_sc}"].get(person, "").split(",") if f.strip()]
                
                for f in foll_list:
                    if G_directed.has_node(f): G_directed.add_edge(f, person)
                for i in ing_list:
                    if G_directed.has_node(i): G_directed.add_edge(person, i)

            # 2. Build G_active with ALL nodes, but ONLY mutual edges
            G_active = nx.Graph()
            for person in G_directed.nodes():
                G_active.add_node(person)

            for u, v in G_directed.edges():
                if G_directed.has_edge(v, u):  # Reciprocal follow check
                    G_active.add_edge(u, v)

            # 3. Calculate 3D positions (Mutual nodes pull inward; Non-mutual float as scatter stars)
            if len(G_active.nodes()) > 0:
                pos_active = nx.fruchterman_reingold_layout(G_active, dim=3, seed=42)
            else:
                pos_active = {}

            # --- PATHFINDING TRACE LOGIC ---
            shortest_path_nodes = []
            shortest_path_edges = set()
            if active_sc == search_target_sc and path_start_global and path_end_global and path_start_global != path_end_global:
                if G_active.has_node(path_start_global) and G_active.has_node(path_end_global):
                    try:
                        shortest_path_nodes = nx.shortest_path(G_active, source=path_start_global, target=path_end_global)
                        for i in range(len(shortest_path_nodes) - 1):
                            shortest_path_edges.add((shortest_path_nodes[i], shortest_path_nodes[i+1]))
                            shortest_path_edges.add((shortest_path_nodes[i+1], shortest_path_nodes[i]))
                        st.success("Route Found: " + " -> ".join([f"{n}" for n in shortest_path_nodes]))
                    except nx.NetworkXNoPath:
                        st.error("No mutual connection path bridges these nodes.")

            # Metrics Display
            mutual_count = len([n for n, d in G_active.degree() if d > 0])
            scatter_count = len(G_active.nodes()) - mutual_count

            sm1, sm2, sm3 = st.columns(3)
            sm1.metric("Central Mutual Hubs", mutual_count)
            sm2.metric("Scattered Star Nodes", scatter_count)
            sm3.metric("Mutual Link Edges", len(G_active.edges()))

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

            # Separate rendering for Mutual Clusters vs Scattered Background Stars
            mutual_x, mutual_y, mutual_z, mutual_text, mutual_colors, mutual_sizes, mutual_borders = [], [], [], [], [], [], []
            star_x, star_y, star_z, star_text = [], [], [], []

            raw_max = max([deg for node, deg in G_active.degree() if deg > 0], default=1)

            for node in G_active.nodes():
                x, y, z = pos_active[node]
                deg = G_active.degree(node)

                if deg > 0:
                    # Mutual Node (Core Constellation)
                    mutual_x.append(x)
                    mutual_y.append(y)
                    mutual_z.append(z)
                    
                    relative_density_weight = (deg / raw_max)
                    mutual_colors.append(relative_density_weight)
                    mutual_text.append(f"<b>Identity:</b> {node}<br><b>Status:</b> Mutual Reciprocal<br><b>Mutual Connections:</b> {deg}")
                    
                    if active_sc == search_target_sc and node == target_pinpoint_global:
                        mutual_sizes.append(node_size_global * 3.0)
                        mutual_borders.append("#00FFFF")
                    elif active_sc == search_target_sc and node in shortest_path_nodes:
                        mutual_sizes.append(node_size_global * 2.0)
                        mutual_borders.append("#FF3333")
                    elif deg == raw_max:
                        mutual_sizes.append(node_size_global * 2.5)
                        mutual_borders.append("#FFCC00")
                    else:
                        scaled_size = node_size_global + (relative_density_weight ** 2 * 20)
                        mutual_sizes.append(scaled_size)
                        mutual_borders.append("#FFFFFF")
                else:
                    # Non-Mutual Node (Scattered Orbit Star)
                    star_x.append(x)
                    star_y.append(y)
                    star_z.append(z)
                    star_text.append(f"<b>Identity:</b> {node}<br><b>Status:</b> Non-Reciprocal (Scattered Orbit Star)<br><i>Awaiting mutual link...</i>")

            # 1. Render Scattered Background Stars
            if star_x:
                star_trace = go.Scatter3d(
                    x=star_x, y=star_y, z=star_z, mode='markers', hovertext=star_text, hoverinfo='text',
                    marker=dict(
                        size=node_size_global * 0.45,
                        color='#556677',
                        opacity=0.4,
                        line=dict(width=0.5, color='#8899A0')
                    ),
                    name="Scattered Orbit Stars"
                )
                data_traces.append(star_trace)

            # 2. Render Central Mutual Constellation Nodes
            if mutual_x:
                mutual_trace = go.Scatter3d(
                    x=mutual_x, y=mutual_y, z=mutual_z, mode='markers', hovertext=mutual_text, hoverinfo='text',
                    marker=dict(
                        showscale=True, 
                        colorscale=color_theme, 
                        color=mutual_colors, 
                        size=mutual_sizes, 
                        line=dict(width=1.5, color=mutual_borders),
                        cmin=0.0,
                        cmax=1.0,
                        colorbar=dict(
                            title=dict(text="Hub Density", side="top"),
                            tickvals=[0, 0.5, 1.0],
                            ticktext=["Low", "Medium", "Peak Hub"]
                        )
                    ),
                    name="Mutual Connections"
                )
                data_traces.append(mutual_trace)

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
            
            # --- CONVERT GRAPH TO HTML TEMPLATE ---
            fig_json = fig_active.to_json()
            unique_id_tag = f"plot_{active_sc.replace(' ', '_')}"
            
            template_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
                <style>
                    body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background-color: #0E1117; font-family: system-ui, sans-serif; }
                    #render_box { width: 100%; height: 100%; position: relative; }
                    
                    #hud_panel {
                        position: absolute;
                        bottom: 25px;
                        left: 25px;
                        z-index: 9999;
                        display: flex;
                        gap: 10px;
                    }
                    
                    .hud_btn {
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
                    }
                    
                    .hud_btn:hover {
                        background: rgba(255, 255, 255, 0.15);
                        border-color: rgba(255, 255, 255, 0.3);
                    }
                    
                    :-webkit-full-screen #render_box { height: 100vh; }
                    :-moz-full-screen #render_box { height: 100vh; }
                    :fullscreen #render_box { height: 100vh; }
                </style>
            </head>
            <body>
                <div id="render_box">
                    <div id="hud_panel">
                        <div id="control_orbit_btn" class="hud_btn" onclick="toggleOrbit()">Pause Auto-Orbit</div>
                        <div id="control_fs_btn" class="hud_btn" onclick="toggleFullscreen()">View Fullscreen</div>
                    </div>
                    <div id="__UNIQUE_ID__" style="width: 100%; height: 100%;"></div>
                </div>
                
                <script>
                    const plotData = __FIG_JSON__;
                    const chartDomNode = document.getElementById('__UNIQUE_ID__');
                    const orbitBtn = document.getElementById('control_orbit_btn');
                    const containerBox = document.getElementById('render_box');
                    
                    Plotly.newPlot(chartDomNode, plotData.data, plotData.layout, {responsive: true, displayModeBar: true});
                    
                    let radAngle = 0;
                    const radius = 1.7; 
                    let isOrbiting = true;

                    function toggleOrbit() {
                        isOrbiting = !isOrbiting;
                        if(isOrbiting) {
                            orbitBtn.innerHTML = "Pause Auto-Orbit";
                            orbitBtn.style.color = "white";
                            try {
                                const currentEye = chartDomNode._fullLayout.scene.camera.eye;
                                radAngle = Math.atan2(currentEye.y, currentEye.x);
                            } catch(e) {}
                        } else {
                            orbitBtn.innerHTML = "Resume Auto-Orbit (Manual Mode Active)";
                            orbitBtn.style.color = "#00FFFF";
                        }
                    }
                    
                    function toggleFullscreen() {
                        if (!document.fullscreenElement) {
                            containerBox.requestFullscreen().catch(err => {
                                alert(`Error enabling full-screen: ${err.message}`);
                            });
                        } else {
                            document.exitFullscreen();
                        }
                    }
                    
                    document.addEventListener('fullscreenchange', () => {
                        Plotly.Plots.resize(chartDomNode);
                    });

                    function runCameraOrbitLoop() {
                        if (isOrbiting) {
                            radAngle += 0.003; 
                            const nextX = radius * Math.cos(radAngle);
                            const nextY = radius * Math.sin(radAngle);
                            
                            try {
                                Plotly.relayout(chartDomNode, {
                                    'scene.camera.eye': { x: nextX, y: nextY, z: 1.0 }
                                });
                            } catch(err) {}
                        }
                        requestAnimationFrame(runCameraOrbitLoop);
                    }
                    
                    setTimeout(runCameraOrbitLoop, 300);
                </script>
            </body>
            </html>
            """
            
            sandbox_html = template_html.replace("__UNIQUE_ID__", unique_id_tag).replace("__FIG_JSON__", fig_json)
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

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
node_size_global = st.sidebar.slider("Node Base Radius", min_value=4, max_value=20, value=10, step=1)
edge_color_global = st.sidebar.color_picker("Link Line Color", value="#888888")

# --- OPTION 2: SYNTHETIC / MOCK DATA GENERATOR ---
st.sidebar.markdown("---")
with st.sidebar.expander("🎲 Synthetic Network Generator", expanded=False):
    target_sc_gen = st.selectbox("Target Scenario:", scenarios, key="opt2_sc_target")
    generator_type = st.selectbox(
        "Network Topology:", 
        ["Scale-Free (Social Hubs)", "Small-World (Clusters)", "Random Mesh"],
        key="opt2_topo_type"
    )
    num_nodes = st.slider("Node Count:", min_value=5, max_value=50, value=15, key="opt2_node_cnt")
    
    if st.button("Generate Synthetic Constellation", use_container_width=True, key="opt2_gen_btn"):
        if generator_type == "Scale-Free (Social Hubs)":
            m = min(2, num_nodes - 1)
            synth_G = nx.barabasi_albert_graph(num_nodes, m, seed=42)
        elif generator_type == "Small-World (Clusters)":
            synth_G = nx.watts_strogatz_graph(num_nodes, k=min(4, num_nodes - 1), p=0.3, seed=42)
        else:
            synth_G = nx.erdos_renyi_graph(num_nodes, p=0.2, seed=42)

        node_names = [f"User_{i+1}" for i in range(num_nodes)]
        st.session_state[f"people_{target_sc_gen}"] = node_names
        
        friends_dict = {name: "" for name in node_names}
        for u, v in synth_G.edges():
            u_name, v_name = node_names[u], node_names[v]
            
            u_curr = [f.strip() for f in friends_dict[u_name].split(",") if f.strip()]
            if v_name not in u_curr:
                u_curr.append(v_name)
            friends_dict[u_name] = ", ".join(u_curr)
            
            v_curr = [f.strip() for f in friends_dict[v_name].split(",") if f.strip()]
            if u_name not in v_curr:
                v_curr.append(u_name)
            friends_dict[v_name] = ", ".join(v_curr)

        st.session_state[f"friends_{target_sc_gen}"] = friends_dict
        save_persisted_data()
        st.success(f"Generated {num_nodes}-node synthetic network!")
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
                st.session_state[f"friends_{active_sc}"] = {"Jinan": ""}
                save_persisted_data()
                st.rerun()
                
            st.markdown("---")
            
            # --- OPTION 4: COLLABORATIVE / SURVEY INTAKE FORM ---
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
                        existing_conn = [f.strip() for f in st.session_state[f"friends_{active_sc}"].get(user_clean, "").split(",") if f.strip()]
                        
                        for person in known_list:
                            if person not in st.session_state[f"people_{active_sc}"]:
                                st.session_state[f"people_{active_sc}"].append(person)
                                st.session_state[f"friends_{active_sc}"][person] = ""
                            if person not in existing_conn:
                                existing_conn.append(person)
                        
                        st.session_state[f"friends_{active_sc}"][user_clean] = ", ".join(existing_conn)
                        save_persisted_data()
                        st.success(f"Added {user_clean}'s connections to {active_sc}!")
                        st.rerun()

            # --- OPTION 3: INTERACTION & MENTION GRAPH ENGINE ---
            with st.expander("🏷️ Interaction & Mention Ingestion", expanded=False):
                st.caption("Map nodes based on public tags, comments, or mention feeds.")
                
                api_source = st.radio("Data Source:", ["Manual Mention Log", "Graph API Ingestion (Stub)"], horizontal=True, key=f"opt3_src_{active_sc}")
                
                if api_source == "Manual Mention Log":
                    mention_input = st.text_area(
                        "Paste Mention Lines (e.g. 'alice -> bob, charlie'):",
                        placeholder="alice -> bob, charlie\nbob -> charlie",
                        height=100,
                        key=f"opt3_mention_input_{active_sc}"
                    )
                    if st.button("Process Mention Network", use_container_width=True, key=f"opt3_btn_{active_sc}"):
                        for line in mention_input.splitlines():
                            if "->" in line:
                                source, targets = line.split("->")
                                src_clean = source.strip().replace("@", "")
                                tgt_list = [t.strip().replace("@", "") for tt in targets.split(",") for t in tt.split()]
                                
                                if src_clean and src_clean not in st.session_state[f"people_{active_sc}"]:
                                    st.session_state[f"people_{active_sc}"].append(src_clean)
                                    st.session_state[f"friends_{active_sc}"][src_clean] = ""
                                
                                curr_friends = [f.strip() for f in st.session_state[f"friends_{active_sc}"].get(src_clean, "").split(",") if f.strip()]
                                for tgt in tgt_list:
                                    if tgt and tgt not in st.session_state[f"people_{active_sc}"]:
                                        st.session_state[f"people_{active_sc}"].append(tgt)
                                        st.session_state[f"friends_{active_sc}"][tgt] = ""
                                    if tgt and tgt not in curr_friends:
                                        curr_friends.append(tgt)
                                
                                st.session_state[f"friends_{active_sc}"][src_clean] = ", ".join(curr_friends)
                        
                        save_persisted_data()
                        st.success("Interaction map updated!")
                        st.rerun()
                else:
                    st.info("Requires `INSTAGRAM_BUSINESS_ACCOUNT_ID` and `ACCESS_TOKEN` configured in secrets.")
                    st.text_input("Access Token", type="password", key=f"opt3_token_{active_sc}")
                    if st.button("Fetch Public Mentions via Graph API", key=f"opt3_fetch_{active_sc}"):
                        st.warning("Connect your Meta Developer Token above to run live query endpoints.")

            st.markdown("---")

            # --- SCENARIO BETA: MAIN ROOT DATA INGESTION ENGINE ---
            if active_sc == "Scenario Beta":
                import_mode = st.radio("Select Input Method:", ["Raw Clipboard Paste", "File Upload (CSV/JSON/TXT)"], horizontal=True)
                run_ingestion = False
                parsed_handles = []

                if import_mode == "Raw Clipboard Paste":
                    bulk_input = st.text_area("Paste unstructured text or platform data strings here:", height=120, key="global_bulk_import_area")
                    if st.button("Process Clipboard Data", use_container_width=True):
                        normalized_text = bulk_input.replace("\n", " ").replace(",", " ")
                        raw_tokens = normalized_text.split()
                        for token in raw_tokens:
                            clean = token.strip().replace("@", "")
                            if clean.lower() in ["follow", "following", "requested", "remove", "verified", "profile", "posts", "followers", "message"]:
                                continue
                            if clean and all(c.isalnum() or c in "._" for c in clean):
                                if clean not in parsed_handles:
                                    parsed_handles.append(clean)
                        if parsed_handles:
                            run_ingestion = True

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
                                normalized_line = line.replace(",", " ")
                                for token in normalized_line.split():
                                    clean = token.strip().replace("@", "")
                                    if clean and all(c.isalnum() or c in "._" for c in clean):
                                        parsed_handles.append(clean)
                        
                        if st.button("Run Data Aggregation", use_container_width=True):
                            if parsed_handles:
                                run_ingestion = True

                if run_ingestion and parsed_handles:
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
                    st.success(f"Appended {len(parsed_handles)} profiles securely.")
                    st.rerun()
                st.markdown("---")

            # --- DYNAMIC PROFILE ROW ENGINE ---
            current_people = list(st.session_state[f"people_{active_sc}"])
            state_mutated = False

            for person in current_people:
                current_val = st.session_state[f"friends_{active_sc}"].get(person, "")
                box_label = f"Mutual connections of {person}" if active_sc == "Scenario Beta" else f"Connections of {person}"
                
                st.markdown(f"#### {box_label}")
                
                if current_val:
                    st.caption(f"Current Linked Connections: {current_val}")
                else:
                    st.caption("No connections registered.")
                
                local_input = st.text_area(
                    "Paste unstructured text or platform data strings here:", 
                    height=100, 
                    key=f"area_local_{active_sc}_{person}",
                    help="Accepts lists separated by spaces, tabs, commas, or new lines."
                )
                
                if st.button("Process Clipboard Data", key=f"btn_local_{active_sc}_{person}", use_container_width=True):
                    normalized_text = local_input.replace("\n", " ").replace(",", " ")
                    raw_tokens = normalized_text.split()
                    
                    local_parsed = []
                    for token in raw_tokens:
                        clean = token.strip().replace("@", "")
                        if clean.lower() in ["follow", "following", "requested", "remove", "verified", "profile", "posts", "followers", "message"]:
                            continue
                        if clean and all(c.isalnum() or c in "._" for c in clean):
                            if clean not in local_parsed:
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
                
                st.markdown("---")

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
            
            # Safe calculation of relative density mapping
            raw_max = max([G_active.degree(node) for node in G_active.nodes()]) if len(G_active.nodes()) > 0 else 0
            max_degree = raw_max if raw_max > 0 else 1

            for node in G_active.nodes():
                x, y, z = pos_active[node]
                node_x.append(x)
                node_y.append(y)
                node_z.append(z)
                deg = G_active.degree(node)
                
                # Dynamic relative normalization mapping (0.0 - 1.0)
                relative_density_weight = (deg / max_degree)
                node_colors.append(relative_density_weight)
                
                if active_sc == "Scenario Beta" and node != "Jinan":
                    node_text.append(f"<b>Handle:</b> {node}<br><b>Connections:</b> {deg}<br><b>Relative Hub Weight:</b> {relative_density_weight:.2f}<br><i>Expand cross-references below</i>")
                else:
                    node_text.append(f"<b>Identity:</b> {node}<br><b>Connections:</b> {deg}<br><b>Relative Hub Weight:</b> {relative_density_weight:.2f}")
                
                # Dynamic Node Physical Scaling
                if active_sc == search_target_sc and node == target_pinpoint_global:
                    custom_sizes.append(node_size_global * 3.0)
                    border_colors.append("#00FFFF")
                elif active_sc == search_target_sc and node in shortest_path_nodes:
                    custom_sizes.append(node_size_global * 2.0)
                    border_colors.append("#FF3333")
                elif deg == raw_max and raw_max > 0:
                    custom_sizes.append(node_size_global * 2.5)
                    border_colors.append("#FFCC00")
                else:
                    scaled_size = node_size_global + (relative_density_weight ** 2 * 24)
                    custom_sizes.append(scaled_size)
                    border_colors.append("#FFFFFF")

            if node_x:
                node_trace = go.Scatter3d(
                    x=node_x, y=node_y, z=node_z, mode='markers', hovertext=node_text, hoverinfo='text',
                    marker=dict(
                        showscale=True, 
                        colorscale=color_theme, 
                        color=node_colors, 
                        size=custom_

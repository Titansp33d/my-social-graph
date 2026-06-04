import streamlit as st
import json
import os
import urllib.parse
import streamlit.components.v1 as components

# Define the persistent storage file path
SAVE_FILE = "network_data.json"

# Set up page configuration
st.set_page_config(page_title="Multi-Scenario Network Suite", layout="wide")

st.title("🛰️ Multi-Scenario Persistent Social Constellation Suite")
st.markdown("""
* **Persistence Active:** Changes are automatically saved to `network_data.json`.
* **VisJS Physics Engine Active:** The graph will naturally bounce, spin, unfold, and animate itself automatically using native browser graphics acceleration!
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

            # --- DYNAMIC RELATIONSHIP BOX GENERATION ---
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

        with col_graph:
            # --- ASSEMBLE JAVASCRIPT OBJECT DATA ARRAYS ---
            js_nodes = []
            js_edges = []
            
            # Map out nodes and give the main node "Jinan" a distinct visual pop color
            for person in st.session_state[f"people_{active_sc}"]:
                is_jinan = person == "Jinan"
                node_color = "#FF3366" if is_jinan else "#00FFFF"
                node_size = 30 if is_jinan else 18
                label_text = f"⭐ {person}" if is_jinan else f"@{person}" if active_sc == "Scenario Beta" else person
                
                js_nodes.append({
                    "id": person, 
                    "label": label_text, 
                    "color": node_color, 
                    "size": node_size,
                    "font": {"color": "#FFFFFF", "size": 14}
                })
                
            # Wire up line link connections
            edges_tracked = set()
            for person, friends_string in st.session_state[f"friends_{active_sc}"].items():
                friends_list = [f.strip().replace("@", "") for f in friends_string.split(",") if f.strip()]
                for friend in friends_list:
                    if friend in st.session_state[f"people_{active_sc}"]:
                        edge_key = tuple(sorted([person, friend]))
                        if edge_key not in edges_tracked:
                            edges_tracked.add(edge_key)
                            js_edges.append({"from": person, "to": friend, "color": {"color": "#888888", "opacity": 0.6}})

            # Convert to clean stringified JSON structures to send across the iframe bridge safely
            nodes_json = json.dumps(js_nodes)
            edges_json = json.dumps(js_edges)

            # --- RENDER THE INTERACTIVE WEB CANVAS ---
            vis_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <style type="text/css">
                    #network_canvas {{
                        width: 100%;
                        height: 650px;
                        background-color: #0E1117;
                        border: 1px solid #262730;
                        border-radius: 8px;
                    }}
                </style>
            </head>
            <body>
                <div id="network_canvas"></div>
                <script type="text/javascript">
                    const container = document.getElementById('network_canvas');
                    const data = {{
                        nodes: new vis.DataSet({nodes_json}),
                        edges: new vis.DataSet({edges_json})
                    }};
                    
                    const options = {{
                        nodes: {{
                            shape: 'dot',
                            shadow: true
                        }},
                        edges: {{
                            width: 2,
                            shadow: true
                        }},
                        physics: {{
                            stabilization: false,
                            barnesHut: {{
                                gravitationalConstant: -3000,
                                centralGravity: 0.2,
                                springLength: 95,
                                springConstant: 0.04,
                                damping: 0.09
                            }}
                        }},
                        interaction: {{
                            hover: true,
                            dragNodes: true,
                            zoomView: true,
                            dragView: true
                        }}
                    }};
                    
                    const network = new vis.Network(container, data, options);
                </script>
            </body>
            </html>
            """
            
            # Embed the self-sustaining vis.js system directly into the right panel column
            components.html(vis_html, height=660)
            
            # --- DIGITAL IDENTITY CROSS-REFERENCE EXPANDERS ---
            if active_sc == "Scenario Beta" and len(st.session_state[f"people_{active_sc}"]) > 1:
                st.markdown("### 🔍 Profile Reconnaissance Dashboard")
                
                dash_col1, dash_col2 = st.columns(2)
                sorted_profiles = sorted([n for n in st.session_state[f"people_{active_sc}"] if n != "Jinan"])
                
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

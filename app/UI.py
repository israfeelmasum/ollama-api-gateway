"""
Streamlit Dashboard for Testing Ollama API Gateway
Run with: streamlit run test_dashboard.py
"""

import streamlit as st
import requests
import json
from typing import Optional

# Page config
st.set_page_config(
    page_title="Ollama API Gateway Tester",
    page_icon="🤖",
    layout="wide"
)

# Sidebar - Configuration
st.sidebar.title("⚙️ Configuration")
api_url = st.sidebar.text_input(
    "API Base URL",
    value="http://localhost:8000",
    help="Base URL of your Ollama API Gateway"
)
api_key = st.sidebar.text_input(
    "API Key",
    value="",
    type="password",
    help="Your API key from .env file"
)
require_auth = st.sidebar.checkbox("Use Authentication", value=True)

# Headers
def get_headers():
    headers = {"Content-Type": "application/json"}
    if require_auth and api_key:
        headers["X-API-Key"] = api_key
    return headers

# Main title
st.title("🤖 Ollama API Gateway Testing Dashboard")
st.markdown("---")

# Tabs for different tests
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 Chat",
    "🖼️ Vision",
    "📊 Embeddings",
    "📋 Models",
    "❤️ Health",
    "📡 Raw Request"
])

# ============================================================================
# TAB 1: CHAT COMPLETION
# ============================================================================
with tab1:
    st.header("💬 Chat Completion")

    col1, col2 = st.columns([2, 1])

    with col1:
        chat_model = st.text_input("Model Name", value="llama3.2", key="chat_model")

        st.subheader("Messages")
        use_system = st.checkbox("Add System Message", value=True)

        if use_system:
            system_msg = st.text_area(
                "System Message",
                value="You are a helpful AI assistant.",
                height=80,
                key="system_msg"
            )

        user_msg = st.text_area(
            "User Message",
            value="What is artificial intelligence? Explain in 2 sentences.",
            height=120,
            key="user_msg"
        )

    with col2:
        st.subheader("Parameters")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.number_input("Max Tokens", 50, 2000, 150, 50)
        stream_chat = st.checkbox("Enable Streaming", value=False)

    if st.button("🚀 Send Chat Request", type="primary", key="chat_btn"):
        # Prepare messages
        messages = []
        if use_system:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": user_msg})

        # Prepare payload
        payload = {
            "model": chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream_chat
        }

        # Make request
        endpoint = "/api/v1/chat/stream" if stream_chat else "/api/v1/chat/completions"
        url = f"{api_url}{endpoint}"

        with st.spinner("Waiting for response..."):
            try:
                response = requests.post(url, headers=get_headers(), json=payload, stream=stream_chat)

                if response.status_code == 200:
                    st.success("✅ Request Successful!")

                    if stream_chat:
                        st.subheader("Streaming Response:")
                        response_container = st.empty()
                        full_response = ""

                        for line in response.iter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        full_response += data["message"]["content"]
                                        response_container.markdown(full_response)
                                except:
                                    pass
                    else:
                        data = response.json()
                        st.subheader("Response:")

                        # Display message content prominently
                        if "message" in data and "content" in data["message"]:
                            st.markdown(f"**Assistant:** {data['message']['content']}")

                        # Show full response in expandable section
                        with st.expander("📄 Full JSON Response"):
                            st.json(data)

                        # Show metrics
                        if "eval_count" in data:
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Tokens Generated", data.get("eval_count", 0))
                            col2.metric("Prompt Tokens", data.get("prompt_eval_count", 0))
                            if "total_duration" in data:
                                duration_sec = data["total_duration"] / 1_000_000_000
                                col3.metric("Duration", f"{duration_sec:.2f}s")
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)

            except Exception as e:
                st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# TAB 2: VISION
# ============================================================================
with tab2:
    st.header("🖼️ Vision Model Testing")

    col1, col2 = st.columns([2, 1])

    with col1:
        vision_model = st.text_input("Vision Model", value="llava:13b", key="vision_model")
        vision_prompt = st.text_area(
            "Prompt",
            value="Describe what you see in this image.",
            height=100,
            key="vision_prompt"
        )

        # Image upload
        uploaded_file = st.file_uploader(
            "Upload Image",
            type=['png', 'jpg', 'jpeg'],
            key="image_upload"
        )

        # Or paste base64
        st.markdown("**OR** paste base64 image data:")
        base64_image = st.text_area("Base64 Image Data", height=100, key="base64_img")

    with col2:
        st.subheader("Parameters")
        vision_temp = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1, key="vision_temp")
        vision_max = st.number_input("Max Tokens", 50, 1000, 200, 50, key="vision_max")

    if st.button("🚀 Analyze Image", type="primary", key="vision_btn"):
        import base64

        # Get image data
        image_data = None
        if uploaded_file:
            image_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
        elif base64_image:
            image_data = base64_image.strip()

        if not image_data:
            st.warning("⚠️ Please upload an image or provide base64 data")
        else:
            payload = {
                "model": vision_model,
                "prompt": vision_prompt,
                "images": [image_data],
                "temperature": vision_temp,
                "max_tokens": vision_max,
                "stream": False
            }

            url = f"{api_url}/api/v1/vision/chat"

            with st.spinner("Analyzing image..."):
                try:
                    response = requests.post(url, headers=get_headers(), json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Analysis Complete!")

                        st.subheader("Model Response:")
                        st.markdown(f"**{data.get('response', 'No response')}**")

                        with st.expander("📄 Full JSON Response"):
                            st.json(data)
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.code(response.text)

                except Exception as e:
                    st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# TAB 3: EMBEDDINGS
# ============================================================================
with tab3:
    st.header("📊 Embedding Generation")

    col1, col2 = st.columns([3, 1])

    with col1:
        embed_model = st.text_input("Embedding Model", value="nomic-embed-text", key="embed_model")

        embed_mode = st.radio("Mode", ["Single Text", "Batch Texts"], horizontal=True)

        if embed_mode == "Single Text":
            embed_text = st.text_area(
                "Text to Embed",
                value="The quick brown fox jumps over the lazy dog.",
                height=100,
                key="single_embed"
            )
        else:
            embed_texts = st.text_area(
                "Texts (one per line)",
                value="First sentence\nSecond sentence\nThird sentence",
                height=150,
                key="batch_embed"
            )

    with col2:
        st.info("💡 Embeddings are vector representations of text")
        show_full_vectors = st.checkbox("Show Full Vectors", value=False)

    if st.button("🚀 Generate Embeddings", type="primary", key="embed_btn"):
        if embed_mode == "Single Text":
            payload = {
                "model": embed_model,
                "input": embed_text
            }
            url = f"{api_url}/api/v1/embeddings"
        else:
            texts = [t.strip() for t in embed_texts.split('\n') if t.strip()]
            payload = {
                "model": embed_model,
                "inputs": texts
            }
            url = f"{api_url}/api/v1/embeddings/batch"

        with st.spinner("Generating embeddings..."):
            try:
                response = requests.post(url, headers=get_headers(), json=payload)

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Embeddings Generated!")

                    if embed_mode == "Single Text":
                        embeddings_list = data.get("embeddings", [])
                        embedding = embeddings_list[0] if embeddings_list else []
                        st.metric("Vector Dimensions", len(embedding))

                        if show_full_vectors:
                            st.subheader("Embedding Vector:")
                            st.code(json.dumps(embedding[:50], indent=2) + "\n... (truncated)")
                        else:
                            st.info(f"First 10 values: {embedding[:10]}")

                    else:
                        embeddings = data.get("embeddings", [])
                        st.metric("Number of Embeddings", len(embeddings))

                        for i, emb_data in enumerate(embeddings):
                            with st.expander(f"Text {i+1}: {emb_data.get('text', '')[:50]}..."):
                                embedding = emb_data.get("embedding", [])
                                st.write(f"Dimensions: {len(embedding)}")
                                if show_full_vectors:
                                    st.code(json.dumps(embedding[:20], indent=2))
                                else:
                                    st.write(f"Preview: {embedding[:5]}...")

                    with st.expander("📄 Full JSON Response"):
                        st.json(data)

                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)

            except Exception as e:
                st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# TAB 4: MODELS
# ============================================================================
with tab4:
    st.header("📋 Model Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 List All Models", type="primary"):
            url = f"{api_url}/api/v1/models"

            with st.spinner("Fetching models..."):
                try:
                    response = requests.get(url, headers=get_headers())

                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])

                        st.success(f"✅ Found {len(models)} models")

                        # Display as table
                        for model in models:
                            with st.expander(f"🤖 {model.get('name', 'Unknown')}"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Type:** {model.get('type', 'N/A')}")
                                    st.write(f"**Family:** {model.get('family', 'N/A')}")
                                with col_b:
                                    st.write(f"**Size:** {model.get('size_formatted', 'N/A')}")
                                    st.write(f"**Capabilities:** {', '.join(model.get('capabilities', []))}")
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.code(response.text)

                except Exception as e:
                    st.error(f"❌ Request Failed: {str(e)}")

    with col2:
        if st.button("📊 Get Model Catalog"):
            url = f"{api_url}/api/v1/models/catalog"

            with st.spinner("Fetching catalog..."):
                try:
                    response = requests.get(url, headers=get_headers())

                    if response.status_code == 200:
                        data = response.json()
                        model_types = data.get("model_types", {})

                        st.success("✅ Catalog Retrieved!")

                        for model_type, models in model_types.items():
                            if models:
                                st.subheader(f"{model_type.upper()} Models ({len(models)})")
                                for model in models:
                                    st.write(f"- {model.get('name', 'Unknown')}")
                    else:
                        st.error(f"❌ Error: {response.status_code}")

                except Exception as e:
                    st.error(f"❌ Request Failed: {str(e)}")

    st.markdown("---")
    st.subheader("🔍 Get Model Info")

    model_name_info = st.text_input("Model Name", value="llama3.2", key="model_info")

    if st.button("Get Info", key="get_model_info"):
        url = f"{api_url}/api/v1/models/{model_name_info}/info"

        with st.spinner("Fetching model info..."):
            try:
                response = requests.get(url, headers=get_headers())

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Model Info Retrieved!")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {data.get('type', 'N/A')}")
                        st.write(f"**Family:** {data.get('family', 'N/A')}")
                    with col2:
                        st.write(f"**Capabilities:** {', '.join(data.get('capabilities', []))}")

                    st.write("**Recommended Endpoints:**")
                    for endpoint in data.get('recommended_endpoints', []):
                        st.code(endpoint)

                    with st.expander("📄 Full Response"):
                        st.json(data)
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)

            except Exception as e:
                st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# TAB 5: HEALTH
# ============================================================================
with tab5:
    st.header("❤️ Health & Status")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💚 Basic Health Check", type="primary"):
            url = f"{api_url}/api/v1/health"

            try:
                response = requests.get(url)  # No auth required

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "healthy":
                        st.success("✅ System Healthy!")
                    else:
                        st.warning("⚠️ System Degraded")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Gateway Version", data.get("gateway_version", "N/A"))
                    with col_b:
                        st.metric("Ollama Connected", "✅" if data.get("ollama_reachable") else "❌")

                    st.code(f"Ollama URL: {data.get('ollama_url', 'N/A')}")
                else:
                    st.error(f"❌ Error: {response.status_code}")

            except Exception as e:
                st.error(f"❌ Request Failed: {str(e)}")

    with col2:
        if st.button("📊 Detailed Status"):
            url = f"{api_url}/api/v1/health/status"

            try:
                response = requests.get(url, headers=get_headers())

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Status Retrieved!")

                    st.metric("Models Available", data.get("models_available", 0))
                    st.metric("Models Loaded", data.get("models_loaded", 0))

                    if data.get("running_models"):
                        st.subheader("🏃 Running Models:")
                        for model in data["running_models"]:
                            st.write(f"- {model.get('name')} ({model.get('size_vram', 'N/A')})")

                    with st.expander("📄 Full Status"):
                        st.json(data)
                else:
                    st.error(f"❌ Error: {response.status_code}")

            except Exception as e:
                st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# TAB 6: RAW REQUEST
# ============================================================================
with tab6:
    st.header("📡 Raw API Request")
    st.info("💡 Send custom requests to any endpoint")

    col1, col2 = st.columns([2, 1])

    with col1:
        raw_endpoint = st.text_input("Endpoint", value="/api/v1/chat/completions", key="raw_endpoint")
        raw_method = st.selectbox("Method", ["POST", "GET", "PUT", "DELETE"])

        raw_payload = st.text_area(
            "JSON Payload",
            value=json.dumps({
                "model": "llama3.2",
                "messages": [{"role": "user", "content": "Hello!"}]
            }, indent=2),
            height=300,
            key="raw_payload"
        )

    with col2:
        st.subheader("Headers")
        st.code(json.dumps(get_headers(), indent=2))

    if st.button("🚀 Send Request", type="primary", key="raw_btn"):
        url = f"{api_url}{raw_endpoint}"

        try:
            payload = json.loads(raw_payload) if raw_payload else {}

            if raw_method == "GET":
                response = requests.get(url, headers=get_headers())
            elif raw_method == "POST":
                response = requests.post(url, headers=get_headers(), json=payload)
            elif raw_method == "PUT":
                response = requests.put(url, headers=get_headers(), json=payload)
            else:
                response = requests.delete(url, headers=get_headers())

            st.subheader(f"Response: {response.status_code}")

            if response.status_code < 400:
                st.success("✅ Request Successful!")
            else:
                st.error(f"❌ Error: {response.status_code}")

            try:
                st.json(response.json())
            except:
                st.code(response.text)

        except json.JSONDecodeError:
            st.error("❌ Invalid JSON in payload")
        except Exception as e:
            st.error(f"❌ Request Failed: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    🤖 Ollama API Gateway Testing Dashboard | Built with Streamlit
</div>
""", unsafe_allow_html=True)
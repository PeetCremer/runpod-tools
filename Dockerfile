# Start from NVIDIA CUDA 12.6.3 with cuDNN on Ubuntu 24.04
FROM nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set shell to bash for better scripting support
SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    # Install basic dependencies and Python 3.12 from Ubuntu repositories
    apt-get install -y --no-install-recommends \
    aria2 \
    curl \
    git \
    wget \
    libgl1 \
    libglib2.0-0 \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    libpython3.12-dev \
    python3-pip \
    fonts-dejavu-core && \
    # Cleanup
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up virtual environment to be used globally
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up working directory
WORKDIR /workspace

# Install Python dependencies
# Using pip (not pip3) since we're in a venv
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126 && \
    pip install --no-cache-dir comfy-cli diffusers jupyterlab triton sageattention


# Install ComfyUI and dependencies
COPY ./workflow_deps ./workflow_deps
RUN comfy --workspace=ComfyUI --skip-prompt install --nvidia && \
    printf '%s\n' '[default]' 'network_mode = personal_cloud' 'security_level = normal' > ComfyUI/user/__manager/config.ini && \
    test -f ComfyUI/user/__manager/config.ini && \
    # ComfyUI-MMAudio is not indexed
    git -C ComfyUI/custom_nodes clone https://github.com/kijai/ComfyUI-MMAudio && \
    pip install -r ComfyUI/custom_nodes/ComfyUI-MMAudio/requirements.txt && \
    # Install workflow dependencies
    for WORKFLOW_DEPS in workflow_deps/*_deps.json; do comfy --recent node install-deps --deps ${WORKFLOW_DEPS}; done && \
    ComfyUI/.venv/bin/pip install --no-cache-dir pytest

# Notebook to run ComfyUI should be already available in workspace
COPY ./run_comfy.ipynb ./run_comfy.ipynb
COPY ./model_envs.py ./model_envs.py
COPY ./startup_models.py ./startup_models.py

# Expose ports for Jupyter Lab and ComfyUI
EXPOSE 8888
EXPOSE 8188

# Add healthcheck to verify Jupyter Lab is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8888/api || exit 1

# Run optional model downloads, then Jupyterlab
CMD python -m startup_models && jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser --FileContentsManager.delete_to_trash=False --ServerApp.preferred_dir=/workspace --ServerApp.token=${JUPYTER_PASSWORD} --ServerApp.allow_origin=https://${RUNPOD_POD_ID}-8888.proxy.runpod.net
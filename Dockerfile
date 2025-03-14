# Start from NVIDIA CUDA 12.4.1 development image with Ubuntu 22.04
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    # Install basic dependencies
    apt-get install -y --no-install-recommends \
    aria2 \
    curl \
    git \
    software-properties-common \
    wget \
    libgl1 \
    libglib2.0-0 && \
    # Install Python 3.12
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3.12-venv libpython3.12-dev && \
    # Make python3 command point to python3.12
    ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python && \
    # Install pip for Python 3.12 and create symlink
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    ln -sf /usr/local/bin/pip /usr/bin/pip3 && \
    # Cleanup
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Install Python dependencies
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 && \
    pip3 install --no-cache-dir comfy-cli diffusers jupyterlab triton sageattention

# Install ComfyUI and dependencies
RUN comfy --workspace=ComfyUI --skip-prompt install --nvidia

# Install workflow dependencies
COPY ./workflow_deps .
RUN for WORKFLOW_DEPS in workflow_deps/*_deps.json; do comfy --recent node install-deps --deps ${WORKFLOW_DEPS}; done

# Purge pip cache to save space
RUN pip3 cache purge


# Expose ports for JupyterLab
EXPOSE 8888

# Command to run on container startup
SHELL ["/bin/bash", "-c"]
CMD jupyter lab --ip=0.0.0.0 --port=8888 --allow-root --no-browser --FileContentsManager.delete_to_trash=False --ServerApp.preferred_dir=/workspace --ServerApp.token=${JUPYTER_PASSWORD} --ServerApp.allow_origin=https://${RUNPOD_POD_ID}-8888.proxy.runpod.net
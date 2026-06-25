import os

import modal
from dotenv import load_dotenv


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_recommended_env_vars() -> dict[str, str]:
    recommended_vars = [
        "JUPYTER_PASSWORD",
        "HUGGINGFACE_TOKEN",
        "CIVITAI_TOKEN",
        "COMFY_MODEL_ENVS",
        "COMFY_LOCAL_MODEL_ENVS_OVERRIDE",
    ]
    env_vars = {var: os.environ.get(var, "") for var in recommended_vars}
    if not env_vars["HUGGINGFACE_TOKEN"]:
        print(
            "WARNING: Environment variable 'HUGGINGFACE_TOKEN' is not defined. "
            "You may not be able to download models from Hugging Face."
        )

    if not env_vars["CIVITAI_TOKEN"]:
        print(
            "WARNING: Environment variable 'CIVITAI_TOKEN' is not defined. "
            "You may not be able to download models from CivitAI."
        )

    if not env_vars["JUPYTER_PASSWORD"]:
        print(
            "WARNING: Environment variable 'JUPYTER_PASSWORD' is not defined. "
            "Your Jupyter Lab server will not be password protected, which could lead to unauthorized access."
        )

    return env_vars


load_dotenv()
env_vars = get_recommended_env_vars()
custom_image = modal.Image.from_registry(  # pyright: ignore[reportUnknownMemberType]
    "jaezred/runpod-tools@sha256:69271fbf117eed2e7fee343a81d2301f3b68ccc3d17814807e631657ad9bb6c6"
)
if _is_truthy(env_vars.get("COMFY_LOCAL_MODEL_ENVS_OVERRIDE", "")):
    # Optional override for rapid local model list iteration without pushing a new image.
    custom_image = custom_image.add_local_file("model_envs.py", "/workspace/model_envs.py")
custom_image = (
    custom_image.env(env_vars).pip_install(
        "python-dotenv==1.1.0"
    )  # Workaround for modal raising error at container startup
)
app = modal.App()


@app.function(image=custom_image, gpu="L40S", timeout=8 * 60 * 60)  # 8 hours timeout
def run_custom_container() -> None:
    import os
    import subprocess

    print("Running inside custom Docker container!")

    # Forward Jupyter Lab and ComfyUI ports
    with modal.forward(8888) as jupyter_tunnel, modal.forward(8188) as comfyui_tunnel:
        import os
        import subprocess

        print(f"Jupyter Lab tunnel URL: {jupyter_tunnel.url}")
        print(f"ComfyUI tunnel URL: {comfyui_tunnel.url}")
        print("Tunnels are active. Your services should be accessible if running in the container.")

        # Set RUNPOD_POD_ID if not present (for local/Modal runs)
        env = os.environ.copy()
        if "RUNPOD_POD_ID" not in env:
            env["RUNPOD_POD_ID"] = "modal-local"

        # Optionally pre-download models for configured environments
        try:
            subprocess.run(
                ["python", "-m", "startup_models"],
                env=env,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Model pre-download failed: {exc}")

        # Launch Jupyter Lab with the same arguments as in Dockerfile
        jupyter_cmd = [
            "jupyter",
            "lab",
            "--ip=0.0.0.0",
            "--port=8888",
            "--allow-root",
            "--no-browser",
            "--FileContentsManager.delete_to_trash=False",
            "--ServerApp.root_dir=/workspace",
            "--ServerApp.preferred_dir=/workspace",
            f"--ServerApp.token={env.get('JUPYTER_PASSWORD', '')}",
            f"--ServerApp.allow_origin=https://{env['RUNPOD_POD_ID']}-8888.proxy.runpod.net",
        ]
        subprocess.run(jupyter_cmd, env=env, check=True)


@app.local_entrypoint()
def main():
    run_custom_container.remote()

from __future__ import annotations

import os
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping


@dataclass
class UrlEntry:
    url: str
    subdir: str
    out: str | None
    headers: Mapping[str, str]


class Aria2Builder:
    """Helper for building aria2c input files targeting the ComfyUI models directory."""

    def __init__(self, comfyui_models_dir: Path | None = None) -> None:
        self._default_models_dir = comfyui_models_dir or Path("ComfyUI") / "models"
        self.reset()

    def reset(self) -> None:
        self._comfyui_models_dir: Path = self._default_models_dir
        self._huggingface_token = os.environ.get("HUGGINGFACE_TOKEN")
        self._civitai_token = os.environ.get("CIVITAI_TOKEN")
        self._file_path: Path = Path("aria2_input_file.txt")
        self._url_entries: list[UrlEntry] = []

    def comfyui_models_dir(self, comfyui_models_dir: Path) -> None:
        self._comfyui_models_dir = comfyui_models_dir

    def huggingface_token(self, huggingface_token: str) -> None:
        self._huggingface_token = huggingface_token

    def civitai_token(self, civitai_token: str) -> None:
        self._civitai_token = civitai_token

    def file_path(self, file_path: Path) -> None:
        self._file_path = file_path

    def add_url(self, url: str, subdir: str) -> None:
        parsed_url = urllib.parse.urlparse(url)

        headers: dict[str, str] = {}
        if "huggingface.co" in parsed_url.netloc:
            if not self._huggingface_token:
                msg = (
                    "huggingface_token is not set and not specified in "
                    "HUGGINGFACE_TOKEN environment variable."
                )
                raise ValueError(msg)
            headers["Authorization"] = f"Bearer {self._huggingface_token}"
        elif "civitai.com" in parsed_url.netloc:
            if not self._civitai_token:
                msg = (
                    "civitai_token is not set and not specified in "
                    "CIVITAI_TOKEN environment variable."
                )
                raise ValueError(msg)
            url = f"{url}&token={self._civitai_token}"

        out: str | None = None
        if "huggingface.co" in parsed_url.netloc or "github.com" in parsed_url.netloc:
            out = os.path.basename(parsed_url.path)
            if not out:
                msg = (
                    "Could not determine filename from URL for repository that "
                    "requires it to be set explicitly."
                )
                raise ValueError(msg)

        url_entry = UrlEntry(url=url, subdir=subdir, out=out, headers=headers)
        self._url_entries.append(url_entry)

    def build(self) -> Path:
        """Write the aria2 input file and reset internal state."""

        boilerplate_options = {
            "split": "16",
            "max-connection-per-server": "16",
            "min-split-size": "1M",
            "allow-overwrite": "true",
            "continue": "true",
            "auto-file-renaming": "false",
        }

        for entry in self._url_entries:
            target_dir = self._comfyui_models_dir / entry.subdir
            target_dir.mkdir(parents=True, exist_ok=True)

        with self._file_path.open("w", encoding="utf-8") as file:
            for url_entry in self._url_entries:
                options: dict[str, str] = {
                    "dir": str(self._comfyui_models_dir / url_entry.subdir),
                }
                if url_entry.out:
                    options["out"] = url_entry.out
                if url_entry.headers:
                    header_value = "\n".join(
                        f"{key}: {value}" for key, value in url_entry.headers.items()
                    )
                    options["header"] = header_value

                file.write(f"{url_entry.url}\n")
                for option, value in boilerplate_options.items():
                    file.write(f"\t{option}={value}\n")
                for option, value in options.items():
                    file.write(f"\t{option}={value}\n")

        result = self._file_path
        self.reset()
        return result


def _run_aria2c(input_file: Path) -> None:
    try:
        subprocess.run(
            [
                "aria2c",
                "--console-log-level=error",
                "-i",
                str(input_file),
            ],
            check=True,
        )
    except FileNotFoundError:
        print(
            "aria2c executable not found on PATH; skipping automatic model downloads.",
            file=sys.stderr,
        )
    except subprocess.CalledProcessError as exc:
        print(f"aria2c failed for {input_file}: {exc}", file=sys.stderr)


def _register_upscalers(builder: Aria2Builder) -> None:
    builder.file_path(Path("upscalers_aria2.txt"))
    builder.add_url(
        "https://civitai.com/api/download/models/125843?type=Model&format=PickleTensor",
        "upscale_models",
    )
    builder.add_url(
        "https://github.com/Phhofm/models/releases/download/2xNomosUni_span_multijpg_ldl/2xNomosUni_span_multijpg_ldl.safetensors",  # noqa: E501
        "upscale_models",
    )
    builder.add_url(
        "https://github.com/Phhofm/models/releases/download/4xNomos8k_atd_jpg/4xNomos8k_atd_jpg.safetensors",  # noqa: E501
        "upscale_models",
    )


def _register_hunyuan(builder: Aria2Builder) -> None:
    builder.file_path(Path("hunyuan_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/vae/hunyuan_video_vae_bf16.safetensors",  # noqa: E501
        "vae",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1356617?type=Model&format=SafeTensor&size=pruned&fp=fp8",  # noqa: E501
        "diffusion_models",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/HunyuanVideo_repackaged/resolve/main/split_files/text_encoders/llava_llama3_fp8_scaled.safetensors",  # noqa: E501
        "text_encoders",
    )
    builder.add_url(
        "https://huggingface.co/zer0int/LongCLIP-SAE-ViT-L-14/resolve/main/Long-ViT-L-14-GmP-SAE-TE-only.safetensors",  # noqa: E501
        "text_encoders",
    )
    builder.add_url(
        "https://huggingface.co/Kijai/HunyuanVideo_comfy/resolve/main/hunyuan_video_FastVideo_720_fp8_e4m3fn.safetensors",  # noqa: E501
        "diffusion_models",
    )

    # LoRAs
    builder.add_url(
        "https://huggingface.co/Kijai/HunyuanVideo_comfy/resolve/main/hyvideo_FastVideo_LoRA-fp8.safetensors",  # noqa: E501
        "loras",
    )
    builder.add_url(
        "https://huggingface.co/leapfusion-image2vid-test/image2vid-960x544/resolve/main/img2vid544p.safetensors",  # noqa: E501
        "loras",
    )

    builder.add_url(
        "https://civitai.com/api/download/models/1259737?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1261435?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1270232?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1231959?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1299285?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1385168?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1289279?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1239432?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1187802?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1419218?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1435515?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1291865?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1410507?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1188578?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1367561?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1389959?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1501799?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1497241?type=Model&format=SafeTensor",
        "loras",
    )


def _register_flux(builder: Aria2Builder) -> None:
    builder.file_path(Path("flux_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q8_0.gguf",
        "unet",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2274229?type=Model&format=GGUF&size=pruned&fp=fp16",
        "unet",
    )

    builder.add_url(
        "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors",
        "vae",
    )

    builder.add_url(
        "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/zer0int/CLIP-GmP-ViT-L-14/resolve/main/ViT-L-14-TEXT-detail-improved-hiT-GmP-TE-only-HF.safetensors",  # noqa: E501
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/zer0int/CLIP-GmP-ViT-L-14/resolve/main/ViT-L-14-BEST-smooth-GmP-TE-only-HF-format.safetensors",  # noqa: E501
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/zer0int/CLIP-Registers-Gated_MLP-ViT-L-14/resolve/main/ViT-L-14-REG-TE-only-balanced-HF-format-ckpt12.safetensors",  # noqa: E501
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors",
        "clip",
    )

    builder.add_url(
        "https://huggingface.co/ByteDance/Hyper-SD/resolve/main/Hyper-FLUX.1-dev-8steps-lora.safetensors",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/736227?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1047380?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1500495?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/746602?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/931225?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1301668?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/917520?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1321842?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1169319?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1278213?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1093128?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1867123?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1867163?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1865751?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1871038?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1064546?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1069819?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1062916?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1068253?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1066495?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/890482?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1524366?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/928767?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2009929?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1892397?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/1918677?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/755852?type=Model&format=SafeTensor",
        "loras",
    )


def _register_pony(builder: Aria2Builder) -> None:
    builder.file_path(Path("pony_aria2.txt"))

    builder.add_url(
        "https://civitai.com/api/download/models/324524?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "checkpoints",
    )

    builder.add_url(
        "https://huggingface.co/wangfuyun/PCM_Weights/resolve/main/sdxl/pcm_sdxl_normalcfg_8step_converted.safetensors",  # noqa: E501
        "loras",
    )
    builder.add_url(
        "https://huggingface.co/wangfuyun/PCM_Weights/resolve/main/sdxl/pcm_sdxl_normalcfg_16step_converted.safetensors",  # noqa: E501
        "loras",
    )

    builder.add_url(
        "https://civitai.com/api/download/models/418782?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/450029?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/418769?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/398292?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/372898?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/363388?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/341131?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/333607?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/333590?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/333587?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/329446?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/323081?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/302106?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/300686?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/298238?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/298005?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/297988?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/369272?type=Model&format=SafeTensor",
        "loras",
    )

    builder.add_url(
        "https://civitai.com/api/download/models/380277?type=Model&format=PickleTensor",
        "embeddings",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/380277?type=Negative&format=Other",
        "embeddings",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/482268?type=Model&format=PickleTensor",
        "embeddings",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/482268?type=Negative&format=Other",
        "embeddings",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/720175?type=Model&format=SafeTensor",
        "embeddings",
    )


def _register_zimage(builder: Aria2Builder) -> None:
    builder.file_path(Path("zimage_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors?download=true",  # noqa: E501
        "diffusion_models",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors",
        "vae",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors",  # noqa: E501
        "text_encoders",
    )

    builder.add_url(
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/loras/z_image_turbo_distill_patch_lora_bf16.safetensors",  # noqa: E501
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2474435?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2581135?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2471161?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2524532?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2478366?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2524277?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2447989?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2488034?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2536215?type=Model&format=SafeTensor",
        "loras",
    )


def _register_chroma(builder: Aria2Builder) -> None:
    builder.file_path(Path("chroma_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/lodestones/Chroma/resolve/main/chroma-unlocked-v50.safetensors",
        "unet",
    )
    builder.add_url(
        "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors",
        "vae",
    )
    builder.add_url(
        "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors",
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/silveroxides/Chroma-LoRA-Experiments/resolve/main/chroma-unlocked-rescaled_cfg_LoRA-rank_16-fp32.safetensors",  # noqa: E501
        "loras",
    )


def _register_qwen_image(builder: Aria2Builder) -> None:
    builder.file_path(Path("qwen_image_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors",  # noqa: E501
        "diffusion_models",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors",  # noqa: E501
        "vae",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors",  # noqa: E501
        "text_encoders",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2195978?type=Model&format=SafeTensor",
        "loras",
    )


def _register_wan(builder: Aria2Builder) -> None:
    builder.file_path(Path("wan_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors",  # noqa: E501
        "diffusion_models",
    )
    builder.add_url(
        "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/I2V/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors",  # noqa: E501
        "diffusion_models",
    )

    builder.add_url(
        "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors",
        "clip",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors",  # noqa: E501
        "clip_vision",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2039365?type=Model&format=SafeTensor&size=full&fp=fp16",
        "clip_vision",
    )
    builder.add_url(
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",  # noqa: E501
        "vae",
    )

    builder.add_url(
        "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/high_noise_model.safetensors",  # noqa: E501
        "loras",
    )
    builder.add_url(
        "https://huggingface.co/lightx2v/Wan2.2-Lightning/resolve/main/Wan2.2-I2V-A14B-4steps-lora-rank64-Seko-V1/low_noise_model.safetensors",  # noqa: E501
        "loras",
    )

    builder.add_url(
        "https://civitai.com/api/download/models/2209275?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2209481?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2230125?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2230133?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2098405?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2098396?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2235299?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2235288?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2176505?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2190476?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2116008?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2116027?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2152516?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2152583?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2156392?type=Model&format=SafeTensor",
        "loras",
    )
    builder.add_url(
        "https://civitai.com/api/download/models/2156435?type=Model&format=SafeTensor",
        "loras",
    )


def _register_mmaudio(builder: Aria2Builder) -> None:
    builder.file_path(Path("mmaudio_aria2.txt"))

    builder.add_url(
        "https://huggingface.co/Kijai/MMAudio_safetensors/resolve/main/apple_DFN5B-CLIP-ViT-H-14-384_fp16.safetensors",  # noqa: E501
        "mmaudio",
    )
    builder.add_url(
        "https://huggingface.co/Kijai/MMAudio_safetensors/resolve/main/mmaudio_large_44k_v2_fp16.safetensors",  # noqa: E501
        "mmaudio",
    )
    builder.add_url(
        "https://huggingface.co/phazei/NSFW_MMaudio/resolve/main/mmaudio_large_44k_nsfw_gold_8.5k_final_fp16.safetensors",  # noqa: E501
        "mmaudio",
    )
    builder.add_url(
        "https://huggingface.co/Kijai/MMAudio_safetensors/resolve/main/mmaudio_synchformer_fp16.safetensors",  # noqa: E501
        "mmaudio",
    )
    builder.add_url(
        "https://huggingface.co/Kijai/MMAudio_safetensors/resolve/main/mmaudio_vae_44k_fp16.safetensors",  # noqa: E501
        "mmaudio",
    )


_ENV_REGISTRARS: dict[str, Callable[[Aria2Builder], None]] = {
    "upscalers": _register_upscalers,
    "hunyuan": _register_hunyuan,
    "flux": _register_flux,
    "pony": _register_pony,
    "zimage": _register_zimage,
    "chroma": _register_chroma,
    "qwen_image": _register_qwen_image,
    "wan": _register_wan,
    "mmaudio": _register_mmaudio,
}

_ENV_ALIASES: dict[str, str] = {
    "upscaler": "upscalers",
    "flux": "flux",
    "pony": "pony",
    "wan": "wan",
    "wan2.2": "wan",
    "wan2_2": "wan",
    "z_image": "zimage",
    "zimage": "zimage",
    "chroma": "chroma",
    "qwen": "qwen_image",
    "qwen-image": "qwen_image",
    "qwen_image": "qwen_image",
    "mmaudio": "mmaudio",
}


def _normalize_env_name(name: str) -> str | None:
    key = name.strip().lower()
    if not key:
        return None
    if key in _ENV_REGISTRARS:
        return key
    return _ENV_ALIASES.get(key)


def list_available_envs() -> list[str]:
    """Return the list of canonical environment names supported by this module."""

    return sorted(_ENV_REGISTRARS)


def download_models_for_envs(
    envs: Iterable[str],
    *,
    models_dir: Path | None = None,
) -> None:
    """Download models for the given logical environments using aria2c.

    Unknown environment names raise ValueError so callers (like the CLI)
    can decide whether to treat them as fatal.
    """

    normalized_envs: list[str] = []
    for raw in envs:
        canonical = _normalize_env_name(raw)
        if canonical is None:
            msg = f"Unknown model environment: {raw!r}"
            raise ValueError(msg)
        normalized_envs.append(canonical)

    if not normalized_envs:
        print("No valid model environments specified; nothing to download.")
        return

    base_dir = models_dir or Path("ComfyUI") / "models"
    builder = Aria2Builder(comfyui_models_dir=base_dir)

    for env_name in normalized_envs:
        registrar = _ENV_REGISTRARS[env_name]
        try:
            registrar(builder)
            input_file = builder.build()
        except ValueError as exc:
            print(
                f"Skipping environment {env_name!r} due to configuration error: {exc}",
                file=sys.stderr,
            )
            continue

        _run_aria2c(input_file)


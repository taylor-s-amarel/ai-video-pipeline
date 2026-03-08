"""Image generation supporting multiple free and paid providers.

Providers (free):
- cloudflare: Cloudflare Workers AI — FLUX 1/2, SD XL, Dreamshaper, Leonardo (10K neurons/day)
- novita: Novita AI — SDXL, SD 1.5, many fine-tunes (free tier)
- stable_horde: Stable Horde — distributed SD/FLUX (free, community GPUs)
- pollinations: Pollinations.ai — FLUX (free, no key, can be slow)

Providers (paid):
- together: Together.ai — FLUX.1 Schnell
- dalle: OpenAI DALL-E 3
- stability: Stability AI — SD3

Models available via Cloudflare:
  @cf/black-forest-labs/flux-1-schnell, @cf/black-forest-labs/flux-2-klein-4b,
  @cf/black-forest-labs/flux-2-klein-9b, @cf/black-forest-labs/flux-2-dev,
  @cf/stabilityai/stable-diffusion-xl-base-1.0, @cf/bytedance/stable-diffusion-xl-lightning,
  @cf/lykon/dreamshaper-8-lcm, @cf/leonardo/phoenix-1.0, @cf/leonardo/lucid-origin

Models available via Novita:
  sd_xl_base_1.0.safetensors, dreamshaper_8_93211.safetensors,
  protovisionXLHighFidelity3D_releaseV660Bakedvae_131308.safetensors,
  realisticVisionV60B1_v51VAE_94301.safetensors, and many more
"""

import time
import base64
import httpx
from pathlib import Path
from dataclasses import dataclass

from config.settings import settings


@dataclass
class ImageResult:
    file_path: Path
    width: int
    height: int
    provider: str


def generate_image(prompt: str, output_path: str | Path,
                    width: int = 1792, height: int = 1024,
                    provider: str | None = None) -> ImageResult:
    """Generate an image using the configured or specified provider."""
    provider = provider or settings.image_provider

    generators = {
        "cloudflare": _cloudflare_generate,
        "novita": _novita_generate,
        "stable_horde": _stable_horde_generate,
        "pollinations": _pollinations_generate,
        "together": _together_generate,
        "dalle": _dalle_generate,
        "stability": _stability_generate,
    }

    if provider not in generators:
        raise ValueError(f"Unknown image provider: {provider}. "
                        f"Available: {', '.join(generators.keys())}")

    return generators[provider](prompt, output_path, width, height)


def _cloudflare_generate(prompt: str, output_path: str | Path,
                          width: int, height: int) -> ImageResult:
    """Cloudflare Workers AI — FLUX, SD XL, Dreamshaper, Leonardo. Free tier."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = settings.image_model or "@cf/black-forest-labs/flux-1-schnell"
    account_id = settings.cloudflare_account_id

    payload = {"prompt": prompt, "num_steps": 4}

    resp = httpx.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
        headers={"Authorization": f"Bearer {settings.cloudflare_api_key}"},
        json=payload,
        timeout=180,
    )
    resp.raise_for_status()

    ct = resp.headers.get("content-type", "")
    if "image" in ct:
        image_bytes = resp.content
    else:
        # JSON response with base64 image
        data = resp.json()
        b64 = data.get("result", {}).get("image", "")
        if not b64:
            raise RuntimeError(f"Cloudflare returned no image: {data}")
        image_bytes = base64.b64decode(b64)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    # Cloudflare FLUX returns 1024x1024 by default
    out_w = width if width <= 1024 else 1024
    out_h = height if height <= 1024 else 1024

    return ImageResult(file_path=output_path, width=out_w, height=out_h,
                       provider="cloudflare")


def _novita_generate(prompt: str, output_path: str | Path,
                      width: int, height: int) -> ImageResult:
    """Novita AI — SDXL, SD 1.5, many fine-tuned models. Free tier."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = settings.image_model or "sd_xl_base_1.0.safetensors"

    # Snap to multiples of 8
    nov_w = min(max((width // 8) * 8, 512), 1536)
    nov_h = min(max((height // 8) * 8, 512), 1536)

    # Submit async generation
    resp = httpx.post(
        "https://api.novita.ai/v3/async/txt2img",
        headers={
            "Authorization": f"Bearer {settings.novita_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "extra": {"response_image_type": "png"},
            "request": {
                "model_name": model,
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, watermark, text",
                "width": nov_w,
                "height": nov_h,
                "steps": 20,
                "guidance_scale": 7,
                "sampler_name": "Euler a",
                "image_num": 1,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["task_id"]

    # Poll for completion (max 3 minutes)
    for _ in range(36):
        time.sleep(5)
        status = httpx.get(
            f"https://api.novita.ai/v3/async/task-result?task_id={task_id}",
            headers={"Authorization": f"Bearer {settings.novita_api_key}"},
            timeout=15,
        ).json()

        task_status = status.get("task", {}).get("status", "")
        if task_status == "TASK_STATUS_SUCCEED":
            images = status.get("images", [])
            if not images:
                raise RuntimeError("Novita returned no images")
            image_url = images[0]["image_url"]
            image_data = httpx.get(image_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(image_data)
            return ImageResult(file_path=output_path, width=nov_w, height=nov_h,
                               provider="novita")
        if task_status == "TASK_STATUS_FAILED":
            reason = status.get("task", {}).get("reason", "unknown")
            raise RuntimeError(f"Novita generation failed: {reason}")

    raise TimeoutError("Novita generation timed out after 3 minutes")


def _together_generate(prompt: str, output_path: str | Path,
                        width: int, height: int) -> ImageResult:
    """Together.ai — FLUX Schnell, free tier available."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # FLUX Schnell supports specific sizes, snap to nearest 64
    flux_w = min(max((width // 64) * 64, 256), 1440)
    flux_h = min(max((height // 64) * 64, 256), 1440)

    model = settings.image_model or "black-forest-labs/FLUX.1-schnell-Free"

    resp = httpx.post(
        "https://api.together.xyz/v1/images/generations",
        headers={
            "Authorization": f"Bearer {settings.together_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "prompt": prompt,
            "width": flux_w,
            "height": flux_h,
            "steps": 4,
            "n": 1,
            "response_format": "b64_json",
        },
        timeout=120,
    )
    resp.raise_for_status()

    b64_data = resp.json()["data"][0]["b64_json"]
    image_bytes = base64.b64decode(b64_data)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return ImageResult(file_path=output_path, width=flux_w, height=flux_h,
                       provider="together")


def _stable_horde_generate(prompt: str, output_path: str | Path,
                            width: int, height: int) -> ImageResult:
    """Stable Horde — free distributed image generation (SD/FLUX)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use first available key or anonymous
    api_keys = settings.stable_horde_api_keys
    api_key = api_keys.split(",")[0].strip() if api_keys else "0000000000"

    # Snap to multiples of 64
    sd_w = min(max((width // 64) * 64, 384), 1024)
    sd_h = min(max((height // 64) * 64, 384), 1024)

    # Use a popular model with available workers
    model = settings.image_model or "AlbedoBase XL (SDXL)"

    # Submit generation request
    resp = httpx.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers={
            "apikey": api_key,
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt + " ### blurry, low quality, watermark",
            "params": {
                "width": sd_w,
                "height": sd_h,
                "steps": 25,
                "cfg_scale": 7,
                "sampler_name": "k_euler_a",
            },
            "models": [model],
            "nsfw": False,
            "r2": True,
        },
        timeout=30,
    )
    resp.raise_for_status()
    job_id = resp.json()["id"]

    # Poll for completion (max 8 minutes for distributed generation)
    for _ in range(96):
        time.sleep(5)
        status = httpx.get(
            f"https://stablehorde.net/api/v2/generate/check/{job_id}",
            timeout=15,
        ).json()

        if status.get("done"):
            break
        if status.get("faulted"):
            raise RuntimeError(f"Stable Horde generation faulted: {status}")
    else:
        raise TimeoutError("Stable Horde generation timed out after 8 minutes")

    # Fetch result
    result = httpx.get(
        f"https://stablehorde.net/api/v2/generate/status/{job_id}",
        timeout=30,
    ).json()

    generations = result.get("generations", [])
    if not generations:
        raise RuntimeError("Stable Horde returned no generations")

    image_url = generations[0]["img"]
    image_data = httpx.get(image_url, timeout=60).content

    with open(output_path, "wb") as f:
        f.write(image_data)

    return ImageResult(file_path=output_path, width=sd_w, height=sd_h,
                       provider="stable_horde")


def _pollinations_generate(prompt: str, output_path: str | Path,
                            width: int, height: int) -> ImageResult:
    """Pollinations.ai — completely free, no key needed. Can be slow."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)

    poll_w = min(max(width, 256), 2048)
    poll_h = min(max(height, 256), 2048)

    model = settings.image_model or "flux"

    url = (f"https://image.pollinations.ai/prompt/{encoded_prompt}"
           f"?width={poll_w}&height={poll_h}&model={model}&nologo=true&seed=-1")

    resp = httpx.get(url, timeout=300, follow_redirects=True)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    return ImageResult(file_path=output_path, width=poll_w, height=poll_h,
                       provider="pollinations")


def _dalle_generate(prompt: str, output_path: str | Path,
                     width: int, height: int) -> ImageResult:
    """OpenAI DALL-E 3 — paid."""
    import openai

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = openai.OpenAI(api_key=settings.openai_api_key)

    # DALL-E 3 only supports specific sizes
    if width > height:
        size = "1792x1024"
        out_w, out_h = 1792, 1024
    elif height > width:
        size = "1024x1792"
        out_w, out_h = 1024, 1792
    else:
        size = "1024x1024"
        out_w, out_h = 1024, 1024

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="hd",
        n=1,
    )

    image_url = response.data[0].url
    image_data = httpx.get(image_url, timeout=60).content

    with open(output_path, "wb") as f:
        f.write(image_data)

    return ImageResult(file_path=output_path, width=out_w, height=out_h,
                       provider="dalle")


def _stability_generate(prompt: str, output_path: str | Path,
                          width: int, height: int) -> ImageResult:
    """Stability AI — paid."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    resp = httpx.post(
        "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={
            "Authorization": f"Bearer {settings.stability_api_key}",
            "Accept": "image/*",
        },
        data={
            "prompt": prompt,
            "output_format": "png",
            "aspect_ratio": "16:9" if width > height else "9:16",
        },
        timeout=120,
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    stab_w = min(max((width // 64) * 64, 320), 1536)
    stab_h = min(max((height // 64) * 64, 320), 1536)

    return ImageResult(file_path=output_path, width=stab_w, height=stab_h,
                       provider="stability")


def list_image_providers() -> dict[str, bool]:
    """Return all image providers and whether they're available."""
    return {
        "cloudflare": bool(settings.cloudflare_api_key and settings.cloudflare_account_id),
        "novita": bool(settings.novita_api_key),
        "together": bool(settings.together_api_key),
        "stable_horde": True,  # Works with anonymous key
        "pollinations": True,  # No key needed
        "dalle": bool(settings.openai_api_key),
        "stability": bool(settings.stability_api_key),
    }

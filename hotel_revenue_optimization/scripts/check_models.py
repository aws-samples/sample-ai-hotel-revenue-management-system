#!/usr/bin/env python3
"""Check that every model in src/hotel_revenue_optimization/utils/model_config.py answers on Amazon Bedrock.

Run it after changing models, after upgrading boto3 or the AgentCore packages, and before a release:

    python scripts/check_models.py                    # every provider (AMAZON, ANTHROPIC, HYBRID)
    python scripts/check_models.py --provider AMAZON  # one provider

It uses your AWS credentials and AWS_REGION (default us-east-1), and the same model IDs, inference profile
prefix (BEDROCK_INFERENCE_PROFILE_PREFIX), Claude effort (BEDROCK_CLAUDE_EFFORT) and MODEL_* overrides as the crew. Each check is one short Converse
call. Exit code 0 when every model answered, 1 otherwise.
"""
import argparse
import importlib.util
import os
import sys

import boto3

UTILS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "hotel_revenue_optimization", "utils")


def _load(name):
    # Load the two modules by path, without importing the package (its __init__ starts the crew's services)
    spec = importlib.util.spec_from_file_location(name, os.path.join(UTILS, f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


model_config = _load("model_config")
wrapper = _load("nova_model_wrapper")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--provider", choices=["AMAZON", "ANTHROPIC", "HYBRID"], action="append",
                        help="provider to check (repeatable); default: all three")
    args = parser.parse_args()
    providers = args.provider or ["AMAZON", "ANTHROPIC", "HYBRID"]

    region = os.environ.get("AWS_REGION", "us-east-1")
    runtime = boto3.client("bedrock-runtime", region_name=region)
    print(f"Region {region}, inference profile prefix {os.environ.get('BEDROCK_INFERENCE_PROFILE_PREFIX', 'us')}")

    # model ID -> where it is used
    usage = {}
    saved = os.environ.get("MODEL_PROVIDER")
    try:
        for provider in providers:
            os.environ["MODEL_PROVIDER"] = provider
            # Every tier (fallbacks use tier3 and tier4) and every agent's effective model, which
            # MODEL_<AGENT> and <AGENT>_LLM_TIER can change
            for tier, models in model_config.get_active_tiers().items():
                usage.setdefault(models[0], []).append(f"{provider}/{tier}")
            for agent in model_config.DEFAULT_MODEL_ASSIGNMENTS:
                usage.setdefault(model_config.get_model_for_agent(agent), []).append(f"{provider}/{agent}")
    finally:
        if saved is None:
            os.environ.pop("MODEL_PROVIDER", None)
        else:
            os.environ["MODEL_PROVIDER"] = saved

    failures = 0
    for model_id, used_by in usage.items():
        profile_id = wrapper.to_inference_profile_id(model_id)
        config = dict(wrapper.inference_config_for(profile_id), maxTokens=64)
        extra = wrapper.additional_fields_for(profile_id)
        try:
            response = runtime.converse(
                modelId=profile_id,
                messages=[{"role": "user", "content": [{"text": "Reply with the single word OK."}]}],
                inferenceConfig=config,
                **({"additionalModelRequestFields": extra} if extra else {}),
            )
            text = "".join(b.get("text", "") for b in response["output"]["message"]["content"]).strip()
            if not text:
                # For example a reasoning-only answer cut off by maxTokens: the crew would get no text either
                raise RuntimeError(f"no answer text (stopReason={response.get('stopReason')})")
            print(f"PASS  {profile_id:<40} {', '.join(used_by)}  -> {text[:20]!r}")
        except Exception as e:  # noqa: BLE001 - report every failure and keep going
            failures += 1
            print(f"FAIL  {profile_id:<40} {', '.join(used_by)}  -> {type(e).__name__}: {e}")

    print("All models answered." if not failures else f"{failures} model(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

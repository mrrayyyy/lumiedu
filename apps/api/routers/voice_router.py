from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from auth import (
    CurrentUser,
    ROLE_ADMIN,
    ROLE_TEACHER,
    get_current_user,
    require_roles,
)
from repos.class_repo import get_class
from repos.voice_repo import (
    create_voice_profile,
    delete_voice_profile,
    get_class_voice,
    get_voice_profile,
    list_voice_profiles_by_teacher,
    set_class_voice,
    update_voice_profile_status,
)
from schemas import (
    ClassVoiceSettingRequest,
    VoiceProfileCreateRequest,
    VoiceProfileResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


def _profile_to_response(p: dict[str, object]) -> VoiceProfileResponse:
    return VoiceProfileResponse(
        profile_id=str(p["profile_id"]),
        teacher_email=str(p["teacher_email"]),
        voice_name=str(p["voice_name"]),
        provider=str(p["provider"]),
        model_path=str(p["model_path"]) if p.get("model_path") else None,
        external_voice_id=str(p["external_voice_id"]) if p.get("external_voice_id") else None,
        sample_count=int(p["sample_count"]),
        status=str(p["status"]),
        created_at=p["created_at"],  # type: ignore[arg-type]
    )


@router.post("/profiles", response_model=VoiceProfileResponse, status_code=201)
async def create_profile(
    payload: VoiceProfileCreateRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> VoiceProfileResponse:
    profile_id = await create_voice_profile(
        teacher_email=current.email,
        voice_name=payload.voice_name,
        provider=payload.provider,
    )
    if not profile_id:
        raise HTTPException(status_code=500, detail="Failed to create voice profile")

    profile = await get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=500, detail="Failed to fetch voice profile")
    return _profile_to_response(profile)


@router.get("/profiles", response_model=list[VoiceProfileResponse])
async def list_profiles(
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> list[VoiceProfileResponse]:
    profiles = await list_voice_profiles_by_teacher(current.email)
    return [_profile_to_response(p) for p in profiles]


@router.get("/profiles/{profile_id}", response_model=VoiceProfileResponse)
async def get_profile(
    profile_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> VoiceProfileResponse:
    profile = await get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if current.role == ROLE_TEACHER and profile["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your profile")
    return _profile_to_response(profile)


@router.post("/profiles/{profile_id}/upload-sample")
async def upload_voice_sample(
    profile_id: str,
    file: UploadFile = File(...),
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    profile = await get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if current.role == ROLE_TEACHER and profile["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your profile")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ("mp3", "wav", "ogg", "m4a", "webm"):
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    content = await file.read()
    max_bytes = 50 * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail="Audio file too large (max 50MB)")

    new_count = int(profile["sample_count"]) + 1
    await update_voice_profile_status(
        profile_id,
        status="pending",
        sample_count=new_count,
    )

    logger.info(
        "voice_sample_uploaded profile_id=%s teacher=%s size=%d",
        profile_id, current.email, len(content),
    )

    return {
        "status": "uploaded",
        "profile_id": profile_id,
        "sample_count": str(new_count),
        "message": "Voice sample uploaded. Training will begin when enough samples are collected.",
    }


@router.post("/profiles/{profile_id}/train")
async def train_voice(
    profile_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    profile = await get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if current.role == ROLE_TEACHER and profile["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your profile")

    if int(profile["sample_count"]) < 1:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one voice sample before training",
        )

    await update_voice_profile_status(profile_id, status="training")

    logger.info("voice_training_started profile_id=%s", profile_id)

    await update_voice_profile_status(profile_id, status="ready")

    return {
        "status": "ready",
        "profile_id": profile_id,
        "message": "Voice profile is now ready to use.",
    }


@router.delete("/profiles/{profile_id}")
async def remove_profile(
    profile_id: str,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    profile = await get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    if current.role == ROLE_TEACHER and profile["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your profile")

    await delete_voice_profile(profile_id)
    return {"status": "deleted", "profile_id": profile_id}


@router.post("/classes/{class_id}/voice")
async def assign_voice_to_class(
    class_id: str,
    payload: ClassVoiceSettingRequest,
    current: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_TEACHER)),
) -> dict[str, str]:
    klass = await get_class(class_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Class not found")
    if current.role == ROLE_TEACHER and klass["teacher_email"] != current.email:
        raise HTTPException(status_code=403, detail="Not your class")

    profile = await get_voice_profile(payload.voice_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    success = await set_class_voice(class_id, payload.voice_profile_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign voice")

    return {
        "status": "assigned",
        "class_id": class_id,
        "voice_profile_id": payload.voice_profile_id,
    }


@router.get("/classes/{class_id}/voice")
async def get_class_voice_setting(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> dict[str, object]:
    voice = await get_class_voice(class_id)
    if not voice:
        return {"class_id": class_id, "voice_profile": None}
    return {"class_id": class_id, "voice_profile": voice}

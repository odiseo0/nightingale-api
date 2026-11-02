from fastapi import APIRouter

from src.api.accounts.infrastructure.accounts_api import router as accounts_router
from src.api.accounts.infrastructure.invitations_api import router as invitations_router
from src.api.appointments.infrastructure.appointments_api import (
    router as appointments_router,
)
from src.api.audit.infrastructure.audit_api import router as audit_router
from src.api.authorization.infrastructure.authorization_api import (
    router as authorization_router,
)
from src.api.health import router as health_router
from src.api.patients.infrastructure.contacts_api import router as contacts_router
from src.api.patients.infrastructure.patients_api import router as patients_router
from src.api.schedule.infrastructure.schedule_api import router as schedule_router
from src.api.services.infrastructure.services_api import router as services_router
from src.api.sync.infrastructure.capabilities_api import router as capabilities_router
from src.api.sync.infrastructure.downloads_api import router as downloads_router
from src.api.sync.infrastructure.events_api import router as events_router
from src.api.sync.infrastructure.operations_api import router as operations_router
from src.api.sync.infrastructure.snapshots_api import router as snapshots_router

router = APIRouter()


router.include_router(health_router)
router.include_router(capabilities_router)
router.include_router(authorization_router)
router.include_router(accounts_router)
router.include_router(invitations_router)
router.include_router(audit_router)
router.include_router(operations_router)
router.include_router(downloads_router)
router.include_router(events_router)
router.include_router(snapshots_router)
router.include_router(patients_router)
router.include_router(contacts_router)
router.include_router(services_router)
router.include_router(schedule_router)
router.include_router(appointments_router)

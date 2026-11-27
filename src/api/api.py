from fastapi import APIRouter

from src.api.accounts.infrastructure.accounts_api import router as accounts_router
from src.api.accounts.infrastructure.invitations_api import router as invitations_router
from src.api.analytics.infrastructure.clinical_api import router as analytics_router
from src.api.appointments.infrastructure.appointments_api import (
    router as appointments_router,
)
from src.api.audit.infrastructure.audit_api import router as audit_router
from src.api.authorization.infrastructure.authorization_api import (
    router as authorization_router,
)
from src.api.care_plans.infrastructure.care_plans_api import (
    router as care_plans_router,
)
from src.api.clinical_records.infrastructure.allergies_api import (
    router as allergies_router,
)
from src.api.clinical_records.infrastructure.antecedents_api import (
    router as antecedents_router,
)
from src.api.clinical_records.infrastructure.clinical_api import (
    router as clinical_router,
)
from src.api.clinical_records.infrastructure.conditions_api import (
    router as conditions_router,
)
from src.api.clinical_records.infrastructure.history_api import router as history_router
from src.api.clinical_records.infrastructure.immunizations_api import (
    router as immunizations_router,
)
from src.api.clinical_records.infrastructure.measurements_api import (
    router as measurements_router,
)
from src.api.clinical_records.infrastructure.notes_api import router as notes_router
from src.api.diagnostic_results.infrastructure.reports_api import (
    router as diagnostic_results_router,
)
from src.api.encounters.infrastructure.encounters_api import router as encounters_router
from src.api.health import router as health_router
from src.api.medications.infrastructure.medications_api import (
    router as medications_router,
)
from src.api.patients.infrastructure.contacts_api import router as contacts_router
from src.api.patients.infrastructure.patients_api import router as patients_router
from src.api.schedule.infrastructure.schedule_api import router as schedule_router
from src.api.services.infrastructure.services_api import router as services_router
from src.api.specialties.infrastructure.odontogram_api import (
    router as odontogram_router,
)
from src.api.specialties.infrastructure.templates_api import (
    router as specialties_router,
)
from src.api.subscriptions.infrastructure.catalog_api import (
    router as operator_plans_router,
)
from src.api.subscriptions.infrastructure.quotes_api import (
    operator_rates_router,
    quotes_router,
)
from src.api.subscriptions.infrastructure.reports_api import (
    router as payment_reports_router,
)
from src.api.subscriptions.infrastructure.reviews_api import (
    router as operator_reports_router,
)
from src.api.subscriptions.infrastructure.subscriptions_api import (
    router as account_subscription_router,
)
from src.api.sync.infrastructure.capabilities_api import router as capabilities_router
from src.api.sync.infrastructure.downloads_api import router as downloads_router
from src.api.sync.infrastructure.events_api import router as events_router
from src.api.sync.infrastructure.operations_api import router as operations_router
from src.api.sync.infrastructure.snapshots_api import router as snapshots_router
from src.api.vademecum.infrastructure.monographs_api import (
    router as vademecum_monographs_router,
)
from src.api.vademecum.infrastructure.products_api import (
    router as vademecum_products_router,
)

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
router.include_router(clinical_router)
router.include_router(encounters_router)
router.include_router(conditions_router)
router.include_router(notes_router)
router.include_router(measurements_router)
router.include_router(immunizations_router)
router.include_router(history_router)
router.include_router(antecedents_router)
router.include_router(allergies_router)
router.include_router(patients_router)
router.include_router(contacts_router)
router.include_router(services_router)
router.include_router(schedule_router)
router.include_router(appointments_router)
router.include_router(medications_router)
router.include_router(care_plans_router)
router.include_router(diagnostic_results_router)
router.include_router(specialties_router)
router.include_router(odontogram_router)
router.include_router(analytics_router)
router.include_router(vademecum_products_router)
router.include_router(vademecum_monographs_router)
router.include_router(operator_plans_router)
router.include_router(operator_rates_router)
router.include_router(quotes_router)
router.include_router(payment_reports_router)
router.include_router(operator_reports_router)
router.include_router(account_subscription_router)

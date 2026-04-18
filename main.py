import secrets
import string
from collections import defaultdict
from datetime import datetime

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session, joinedload, selectinload

from database import SessionLocal, get_db
from models import Attendance, AttendanceStatus, Coordenador, Professor, Resident, Session as SessionModel, Team

app = FastAPI()


def _generate_pin() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(4))


@app.get("/")
def root():
    return {"message": "Sistema de presença rodando 🚀"}


@app.post("/residents")
def create_resident(name: str, email: str, db: Session = Depends(get_db)):
    novo_residente = Resident(name=name, email=email, pin=_generate_pin())
    db.add(novo_residente)
    db.commit()
    db.refresh(novo_residente)
    return {"message": "Residente criado com sucesso", "pin": novo_residente.pin}


@app.get("/residents")
def list_residents(db: Session = Depends(get_db)):
    return db.query(Resident).all()


@app.post("/professors")
def create_professor(name: str, email: str, db: Session = Depends(get_db)):
    professor = Professor(name=name, email=email, pin=_generate_pin())
    db.add(professor)
    db.commit()
    db.refresh(professor)
    return {"message": "Professor criado", "pin": professor.pin}


@app.post("/teams")
def create_team(name: str, professor_id: int, db: Session = Depends(get_db)):
    team = Team(name=name, professor_id=professor_id)
    db.add(team)
    db.commit()
    return {"message": "Equipe criada"}


@app.put("/residents/{resident_id}/team")
def assign_team(resident_id: int, team_id: int, db: Session = Depends(get_db)):
    resident = db.query(Resident).get(resident_id)
    resident.team_id = team_id
    db.commit()
    return {"message": "Residente vinculado à equipe"}


@app.post("/sessions")
def create_session(description: str, date: str, db: Session = Depends(get_db)):
    session = SessionModel(
        description=description,
        date=datetime.strptime(date, "%Y-%m-%d"),
    )
    db.add(session)
    db.commit()
    return {"message": "Sessão criada"}


@app.post("/attendance")
def register_attendance(
    resident_id: int,
    session_id: int,
    status_id: int,
    justification: str = None,
    db: Session = Depends(get_db),
):
    existing = db.query(Attendance).filter(
        Attendance.resident_id == resident_id,
        Attendance.session_id == session_id,
    ).first()

    if existing:
        existing.status_id = status_id
        existing.justification = justification
    else:
        db.add(Attendance(
            resident_id=resident_id,
            session_id=session_id,
            status_id=status_id,
            justification=justification,
        ))

    db.commit()
    return {"message": "Presença registrada"}


@app.get("/attendance")
def list_attendance(db: Session = Depends(get_db)):
    records = (
        db.query(Attendance)
        .options(
            joinedload(Attendance.resident),
            joinedload(Attendance.session),
            joinedload(Attendance.status),
        )
        .all()
    )
    return [
        {
            "id": r.id,
            "resident": r.resident.name,
            "session": r.session.description,
            "date": str(r.session.date),
            "status": r.status.name,
            "justification": r.justification,
        }
        for r in records
    ]


@app.get("/residents/{resident_id}/attendance")
def get_resident_attendance(resident_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(Attendance)
        .options(joinedload(Attendance.session), joinedload(Attendance.status))
        .filter(Attendance.resident_id == resident_id)
        .all()
    )
    return [
        {
            "session": r.session.description,
            "date": str(r.session.date),
            "status": r.status.name,
            "justification": r.justification,
        }
        for r in records
    ]


@app.get("/residents/by-email")
def get_resident_by_email(email: str, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.email == email).first()
    if not resident:
        return {"error": "Residente não encontrado"}
    return {"id": resident.id, "name": resident.name, "email": resident.email}


@app.get("/attendance/by-email")
def get_attendance_by_email(email: str, db: Session = Depends(get_db)):
    resident = (
        db.query(Resident).filter(Resident.email == email).first()
    )
    if not resident:
        return {"error": "Residente não encontrado"}

    records = (
        db.query(Attendance)
        .options(joinedload(Attendance.session), joinedload(Attendance.status))
        .filter(Attendance.resident_id == resident.id)
        .all()
    )
    return [
        {
            "session": r.session.description,
            "date": str(r.session.date),
            "status": r.status.name,
            "justification": r.justification,
        }
        for r in records
    ]


@app.post("/coordenadores")
def create_coordenador(name: str, email: str, db: Session = Depends(get_db)):
    coordenador = Coordenador(name=name, email=email, pin=_generate_pin())
    db.add(coordenador)
    db.commit()
    db.refresh(coordenador)
    return {"message": "Coordenador criado", "pin": coordenador.pin}


@app.get("/coordenadores")
def list_coordenadores(db: Session = Depends(get_db)):
    coordenadores = db.query(Coordenador).order_by(Coordenador.name).all()
    return [
        {"id": c.id, "name": c.name, "email": c.email, "pin": c.pin}
        for c in coordenadores
    ]


@app.post("/auth/login")
def login(email: str, pin: str, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.email == email).first()
    if resident:
        if resident.pin != pin:
            return {"error": "PIN incorreto"}
        return {"role": "resident"}

    professor = db.query(Professor).filter(Professor.email == email).first()
    if professor:
        if professor.pin != pin:
            return {"error": "PIN incorreto"}
        return {"role": "professor"}

    coordenador = db.query(Coordenador).filter(Coordenador.email == email).first()
    if coordenador:
        if coordenador.pin != pin:
            return {"error": "PIN incorreto"}
        return {"role": "coordenador"}

    return {"error": "Usuário não encontrado"}


@app.get("/residents/pins")
def list_resident_pins(db: Session = Depends(get_db)):
    """Lista todos os residentes com seus PINs (uso administrativo)."""
    residents = db.query(Resident).order_by(Resident.name).all()
    return [
        {"id": r.id, "name": r.name, "email": r.email, "pin": r.pin}
        for r in residents
    ]


@app.get("/users/role")
def get_user_role(email: str, db: Session = Depends(get_db)):
    if db.query(Resident).filter(Resident.email == email).first():
        return {"role": "resident"}
    if db.query(Professor).filter(Professor.email == email).first():
        return {"role": "professor"}
    if db.query(Coordenador).filter(Coordenador.email == email).first():
        return {"role": "coordenador"}
    return {"error": "Usuário não encontrado"}


@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).order_by(SessionModel.id.asc()).all()
    return [
        {"id": s.id, "description": s.description, "date": str(s.date)}
        for s in sessions
    ]


@app.get("/attendance-status")
def list_attendance_status(db: Session = Depends(get_db)):
    statuses = db.query(AttendanceStatus).all()
    return [{"id": s.id, "name": s.name} for s in statuses]


@app.get("/teams/by-professor")
def get_teams_by_professor(email: str, db: Session = Depends(get_db)):
    professor = db.query(Professor).filter(Professor.email == email).first()
    if not professor:
        return {"error": "Professor não encontrado"}

    teams = (
        db.query(Team)
        .options(selectinload(Team.residents))
        .filter(Team.professor_id == professor.id)
        .all()
    )
    return [
        {
            "id": team.id,
            "name": team.name,
            "residents": [{"id": r.id, "name": r.name} for r in team.residents],
        }
        for team in teams
    ]


@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    # Carrega times + professor + residentes em 2 queries (sem N+1)
    teams = (
        db.query(Team)
        .options(
            joinedload(Team.professor),
            selectinload(Team.residents),
        )
        .all()
    )

    if not teams:
        return []

    # Busca todas as presenças dos residentes desses times em uma única query
    resident_ids = [r.id for team in teams for r in team.residents]
    all_attendances = (
        db.query(Attendance)
        .options(joinedload(Attendance.status))
        .filter(Attendance.resident_id.in_(resident_ids))
        .all()
    )

    # Agrupa por residente em memória
    attendance_by_resident: dict[int, list] = defaultdict(list)
    for a in all_attendances:
        attendance_by_resident[a.resident_id].append(a)

    response = []
    for team in teams:
        residents_list = []
        for r in team.residents:
            attendances = attendance_by_resident[r.id]
            presencas = sum(1 for a in attendances if a.status.name.lower() == "presente")
            justificadas = sum(
                1 for a in attendances
                if a.status.name.lower() != "presente" and a.justification
            )
            nao_justificadas = sum(
                1 for a in attendances
                if a.status.name.lower() != "presente" and not a.justification
            )
            residents_list.append({
                "name": r.name,
                "presencas": presencas,
                "justificadas": justificadas,
                "nao_justificadas": nao_justificadas,
            })

        response.append({
            "team": team.name,
            "professor": team.professor.name if team.professor else "Sem professor",
            "residents": residents_list,
        })

    return response

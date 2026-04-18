from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Date
from sqlalchemy import UniqueConstraint

Base = declarative_base()


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    pin = Column(String, nullable=True)


class Coordenador(Base):
    __tablename__ = "coordenadores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    pin = Column(String, nullable=True)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    professor_id = Column(Integer, ForeignKey("professors.id"))

    professor = relationship("Professor")
    residents = relationship("Resident", back_populates="team")


class Resident(Base):
    __tablename__ = "residents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    pin = Column(String, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    team = relationship("Team", back_populates="residents")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    description = Column(String)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint('resident_id', 'session_id', name='unique_attendance'),)

    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"))
    session_id = Column(Integer, ForeignKey("sessions.id"))

    status_id = Column(Integer, ForeignKey("attendance_status.id"))
    status = relationship("AttendanceStatus")
    justification = Column(String, nullable=True)


    resident = relationship("Resident")
    session = relationship("Session")
    status = relationship("AttendanceStatus")

class AttendanceStatus(Base):
    __tablename__ = "attendance_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)


from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime

DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/guilhermemacedo"

app = FastAPI()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Pacient(Base):
    __tablename__ = 'pacient'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    vaccines = relationship('Vaccine', back_populates='pacient', cascade="all, delete-orphan")

class Vaccine(Base):
    __tablename__ = 'vaccine'
    id = Column(Integer, primary_key=True, index=True)
    pacient_id = Column(Integer, ForeignKey('pacient.id', ondelete='CASCADE'))
    vaccine_name = Column(String, nullable=False)
    dose_date = Column(DateTime, nullable=False)
    dose_number = Column(Integer, nullable=False)
    vaccine_type = Column(String, nullable=False)
    pacient = relationship('Pacient', back_populates='vaccines')
    doses = relationship('Dose', back_populates='vaccine', cascade="all, delete-orphan")

class Dose(Base):
    __tablename__ = 'dose'
    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, ForeignKey('vaccine.id', ondelete='CASCADE'))
    type_dose = Column(String, nullable=False)
    dose_date = Column(DateTime, nullable=False)
    dose_number = Column(Integer, nullable=False)
    application_type = Column(String, nullable=False)
    vaccine = relationship('Vaccine', back_populates='doses')

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/pacient", response_model=dict)
def create_pacient(name: str, last_name: str, db: Session = Depends(get_db)):
    try:
        pacient = Pacient(name=name, last_name=last_name)
        db.add(pacient)
        db.commit()
        db.refresh(pacient)
        return {"id": pacient.id, "name": pacient.name, "last_name": pacient.last_name}
    except Exception as e:
        print(f"Error creating pacient: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/pacient", response_model=list)
def get_pacients(db: Session = Depends(get_db)):
    try:
        pacients = db.query(Pacient).all()
        return [{"id": pacient.id, "name": pacient.name, "last_name": pacient.last_name} for pacient in pacients]
    except Exception as e:
        print(f"Error fetching pacients: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/pacient/{pacient_id}", response_model=dict)
def get_pacient(pacient_id: int, db: Session = Depends(get_db)):
    try:
        pacient = db.query(Pacient).filter(Pacient.id == pacient_id).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Pacient not found")

        # Cria o dicionário de resposta incluindo vacinas e doses
        result = {
            "id": pacient.id,
            "name": pacient.name,
            "last_name": pacient.last_name,
            "vaccines": []
        }

        for vaccine in pacient.vaccines:
            vaccine_dict = {
                "id": vaccine.id,
                "vaccine_name": vaccine.vaccine_name,
                "dose_date": vaccine.dose_date.isoformat(),
                "dose_number": vaccine.dose_number,
                "vaccine_type": vaccine.vaccine_type,
                "doses": []
            }

            # Adiciona as doses associadas à vacina
            for dose in vaccine.doses:
                dose_dict = {
                    "id": dose.id,
                    "type_dose": dose.type_dose,
                    "dose_date": dose.dose_date.isoformat(),
                    "dose_number": dose.dose_number,
                    "application_type": dose.application_type
                }
                vaccine_dict["doses"].append(dose_dict)
            
            result["vaccines"].append(vaccine_dict)

        return result
    except Exception as e:
        print(f"Error fetching pacient: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/api/pacient/{pacient_id}", response_model=dict)
def update_pacient(pacient_id: int, name: str, last_name: str, db: Session = Depends(get_db)):
    try:
        pacient = db.query(Pacient).filter(Pacient.id == pacient_id).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Pacient not found")
        pacient.name = name
        pacient.last_name = last_name
        db.commit()
        db.refresh(pacient)
        return {"id": pacient.id, "name": pacient.name, "last_name": pacient.last_name}
    except Exception as e:
        print(f"Error updating pacient: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/api/pacient/{pacient_id}", response_model=dict)
def delete_pacient(pacient_id: int, db: Session = Depends(get_db)):
    try:
        pacient = db.query(Pacient).filter(Pacient.id == pacient_id).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Pacient not found")
        db.delete(pacient)
        db.commit()
        return {"message": "Pacient deleted successfully"}
    except Exception as e:
        print(f"Error deleting pacient: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/vaccine", response_model=dict)
def create_vaccine(pacient_id: int, vaccine_name: str, dose_date: str, dose_number: int, vaccine_type: str, db: Session = Depends(get_db)):
    try:
        # Verificar se o paciente existe
        pacient = db.query(Pacient).filter(Pacient.id == pacient_id).first()
        if not pacient:
            raise HTTPException(status_code=404, detail="Pacient not found")
        
        # Converter a data de string para datetime
        dose_date = datetime.strptime(dose_date, '%Y-%m-%d')
        
        vaccine = Vaccine(pacient_id=pacient_id, vaccine_name=vaccine_name, dose_date=dose_date, dose_number=dose_number, vaccine_type=vaccine_type)
        db.add(vaccine)
        db.commit()
        db.refresh(vaccine)
        return {"id": vaccine.id, "pacient_id": vaccine.pacient_id, "vaccine_name": vaccine.vaccine_name, "dose_date": vaccine.dose_date, "dose_number": vaccine.dose_number, "vaccine_type": vaccine.vaccine_type}
    except Exception as e:
        print(f"Error creating vaccine: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/vaccine", response_model=list)
def get_vaccines(db: Session = Depends(get_db)):
    try:
        vaccines = db.query(Vaccine).all()
        return [{"id": vaccine.id, "pacient_id": vaccine.pacient_id, "vaccine_name": vaccine.vaccine_name, "dose_date": vaccine.dose_date, "dose_number": vaccine.dose_number, "vaccine_type": vaccine.vaccine_type} for vaccine in vaccines]
    except Exception as e:
        print(f"Error fetching vaccines: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/vaccine/{vaccine_id}", response_model=dict)
def get_vaccine(vaccine_id: int, db: Session = Depends(get_db)):
    try:
        vaccine = db.query(Vaccine).filter(Vaccine.id == vaccine_id).first()
        if not vaccine:
            raise HTTPException(status_code=404, detail="Vaccine not found")
        result = {"id": vaccine.id, "pacient_id": vaccine.pacient_id, "vaccine_name": vaccine.vaccine_name, "dose_date": vaccine.dose_date, "dose_number": vaccine.dose_number, "vaccine_type": vaccine.vaccine_type, "doses": []}
        result["doses"] = [{"id": dose.id, "type_dose": dose.type_dose, "dose_date": dose.dose_date.isoformat(), "dose_number": dose.dose_number, "application_type": dose.application_type} for dose in vaccine.doses]
        return result
    except Exception as e:
        print(f"Error fetching vaccine: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/api/vaccine/{vaccine_id}", response_model=dict)
def update_vaccine(vaccine_id: int, vaccine_name: str, dose_date: str, dose_number: int, vaccine_type: str, db: Session = Depends(get_db)):
    try:
        vaccine = db.query(Vaccine).filter(Vaccine.id == vaccine_id).first()
        if not vaccine:
            raise HTTPException(status_code=404, detail="Vaccine not found")
        
        # Converter a data de string para datetime
        dose_date = datetime.strptime(dose_date, '%Y-%m-%d')
        
        vaccine.vaccine_name = vaccine_name
        vaccine.dose_date = dose_date
        vaccine.dose_number = dose_number
        vaccine.vaccine_type = vaccine_type
        db.commit()
        db.refresh(vaccine)
        return {"id": vaccine.id, "pacient_id": vaccine.pacient_id, "vaccine_name": vaccine.vaccine_name, "dose_date": vaccine.dose_date, "dose_number": vaccine.dose_number, "vaccine_type": vaccine.vaccine_type}
    except Exception as e:
        print(f"Error updating vaccine: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/api/vaccine/{vaccine_id}", response_model=dict)
def delete_vaccine(vaccine_id: int, db: Session = Depends(get_db)):
    try:
        vaccine = db.query(Vaccine).filter(Vaccine.id == vaccine_id).first()
        if not vaccine:
            raise HTTPException(status_code=404, detail="Vaccine not found")
        db.delete(vaccine)
        db.commit()
        return {"message": "Vaccine deleted successfully"}
    except Exception as e:
        print(f"Error deleting vaccine: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/dose", response_model=dict)
def create_dose(vaccine_id: int, type_dose: str, dose_date: str, dose_number: int, application_type: str, db: Session = Depends(get_db)):
    try:
        # Converter a data de string para datetime
        dose_date = datetime.strptime(dose_date, '%Y-%m-%d')
        
        dose = Dose(vaccine_id=vaccine_id, type_dose=type_dose, dose_date=dose_date, dose_number=dose_number, application_type=application_type)
        db.add(dose)
        db.commit()
        db.refresh(dose)
        return {"id": dose.id, "vaccine_id": dose.vaccine_id, "type_dose": dose.type_dose, "dose_date": dose.dose_date, "dose_number": dose.dose_number, "application_type": dose.application_type}
    except Exception as e:
        print(f"Error creating dose: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/dose", response_model=list)
def get_doses(db: Session = Depends(get_db)):
    try:
        doses = db.query(Dose).all()
        return [{"id": dose.id, "vaccine_id": dose.vaccine_id, "type_dose": dose.type_dose, "dose_date": dose.dose_date, "dose_number": dose.dose_number, "application_type": dose.application_type} for dose in doses]
    except Exception as e:
        print(f"Error fetching doses: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/dose/{dose_id}", response_model=dict)
def get_dose(dose_id: int, db: Session = Depends(get_db)):
    try:
        dose = db.query(Dose).filter(Dose.id == dose_id).first()
        if not dose:
            raise HTTPException(status_code=404, detail="Dose not found")
        return {"id": dose.id, "vaccine_id": dose.vaccine_id, "type_dose": dose.type_dose, "dose_date": dose.dose_date.isoformat(), "dose_number": dose.dose_number, "application_type": dose.application_type}
    except Exception as e:
        print(f"Error fetching dose: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/api/dose/{dose_id}", response_model=dict)
def update_dose(dose_id: int, type_dose: str, dose_date: str, dose_number: int, application_type: str, db: Session = Depends(get_db)):
    try:
        dose = db.query(Dose).filter(Dose.id == dose_id).first()
        if not dose:
            raise HTTPException(status_code=404, detail="Dose not found")
        
        # Converter a data de string para datetime
        dose_date = datetime.strptime(dose_date, '%Y-%m-%d')
        
        dose.type_dose = type_dose
        dose.dose_date = dose_date
        dose.dose_number = dose_number
        dose.application_type = application_type
        db.commit()
        db.refresh(dose)
        return {"id": dose.id, "vaccine_id": dose.vaccine_id, "type_dose": dose.type_dose, "dose_date": dose.dose_date, "dose_number": dose.dose_number, "application_type": dose.application_type}
    except Exception as e:
        print(f"Error updating dose: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/api/dose/{dose_id}", response_model=dict)
def delete_dose(dose_id: int, db: Session = Depends(get_db)):
    try:
        dose = db.query(Dose).filter(Dose.id == dose_id).first()
        if not dose:
            raise HTTPException(status_code=404, detail="Dose not found")
        db.delete(dose)
        db.commit()
        return {"message": "Dose deleted successfully"}
    except Exception as e:
        print(f"Error deleting dose: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


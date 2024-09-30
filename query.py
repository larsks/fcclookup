import os
import dotenv

dotenv.load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from fccdb import *

if __name__ == "__main__":
    engine = create_engine(os.environ["FCC_DBURI"], echo=True)
    Base.metadata.create_all(engine)
    session = Session(engine)

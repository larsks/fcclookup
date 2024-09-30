import os
import dotenv

dotenv.load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry

from fccdb import Base
from fccdb import Entity
from fccdb import Amateur
from fccdb import History
from fccdb import LicenseHeader
from fccdb import Comment
from fccdb import LicenseAttachment
from fccdb import LicenseSpecialCondition
from fccdb import LicenseFreeformSpecialCondition


# @listens_for(Engine, "connect")
# def on_connect(dbapi_con: DBAPIConnection, con_record: ConnectionPoolEntry):
#    cursor = dbapi_con.cursor()
#    cursor.execute("PRAGMA journal_mode=OFF")
#    cursor.execute("PRAGMA synchronous=OFF")
#    cursor.close()


engine = create_engine(os.environ["FCC_DBURI"])
Base.metadata.create_all(engine)
with Session(engine) as session:
    with session.begin():
        print("import entities")
        with open("db/EN.dat", newline="\r\n") as fd:
            Entity.import_csv(fd, session)

    with session.begin():
        print("import amateur")
        with open("db/AM.dat", newline="\r\n") as fd:
            Amateur.import_csv(fd, session)

    with session.begin():
        print("import history")
        with open("db/HS.dat", newline="\r\n") as fd:
            History.import_csv(fd, session)

    with session.begin():
        print("import headers")
        with open("db/HD.dat", newline="\r\n") as fd:
            LicenseHeader.import_csv(fd, session)

    with session.begin():
        print("import comments")
        with open("test.dat", newline="\r\n") as fd:
            Comment.import_csv(fd, session)

    with session.begin():
        print("import attachments")
        with open("db/LA.dat", newline="\r\n") as fd:
            LicenseAttachment.import_csv(fd, session)

    with session.begin():
        print("import special conditions")
        with open("db/SC.dat", newline="\r\n") as fd:
            LicenseSpecialCondition.import_csv(fd, session)

    with session.begin():
        print("import freeform special conditions")
        with open("db/SF.dat", newline="\r\n") as fd:
            LicenseFreeformSpecialCondition.import_csv(fd, session)

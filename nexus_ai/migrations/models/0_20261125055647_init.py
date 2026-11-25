from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "auth_users" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "username" VARCHAR(150) UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "is_active" INT NOT NULL,
    "is_verified" INT NOT NULL,
    "role" VARCHAR(50) NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
) /* Default reusable user model. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztl21P2zAQx79KlFdMYlUp5UHTNKmlnegE7QTpNjFNlhu7jUVih8QBKsZ3n89NmseWFl"
    "EGiDdV+r875/KzffbdmZ4g1A1rw5AG5ifjzuTYo+ohp28bJvb9VAVB4pGrHXEkHRQpNy3j"
    "USgDbEtlGWM3pEoiNLQD5ksmOPh36BhHrjQCGoUwhgGxhh64BiMQYashGJ+s4hxxdhVRJM"
    "WESkd/we8/Smac0FsaJn/9SzRm1CW5D2QEBtA6klNfa8Nhr/NVe0IiI2QLN/J46u1PpSP4"
    "3D2KGKlBDNgmlNMAS0oyn84j1405JdIsYyXIIKLzVEkqkNknw/ifxxG3gZuh3wQ/zS9xah"
    "k3hPoDC513LYTMEm9IoUA1lmzBYa4YlwDq7n42bgpEqya84Oi4dba1u/9BIxChnATaqHGZ"
    "9zoQSzwL1dBTytTDzC2DPnJwUA16HlBgrVLdDOUE0AaQmh6+RS7lE+mov429vSWMf7TONG"
    "blpTkLtYtmG6wfmxozG/BO+cJ+0M9rIM7GPIpyzPAlQt7Zq68AWXkthKxtecgODh1KkI/D"
    "8EYEFXVjMeuK0KdZ2ImQQk/r7dtY2ixE6iBh1xVruy2ESzFfUKqzcQXYIxW4KdrJon/e2t"
    "weDE5gZC8Mr1wt9KwC5OFpu6vWvGavnJjUcq9vlYFf04Cpt1Qs8YeQZyOfEfpcebXUA8V1"
    "nYqS+D9fGdEHxqauHflCslL1XlK8y7XbDijgQFiWIXeURTKPVoPORxZwkzi0ljy8xhquPp"
    "AMuDuNi9cS9FbvtHtutU6/5xZ9p2V1wdLQ6rSgbu0Xpmk+iPGzZx0b8Ne4GPS7xWvl3M+6"
    "MCEn1WEIxMUNwiRzuUjUhFr+WuSTR856PvJ91l/KrCeMMtOus4f+bnyZ6T1AGGH78gYHBJ"
    "UsoiEW+ZZNXsMrKpjjiZ4zgAtpxn1ySx1/tmNWdNCxZXtpD536PNQ/L57nJ+6Fe1yu0Qqr"
    "1VXcC/E+fbnd2QRS+NjYaR40D3f3m4fKRac5Vw6W7I3kIF/c+qobUQgprXG2Z0Leu4TVug"
    "TYVGsQjt3fIN2d+kqdb31J51sv354El5RXHKLfzgf9BdemNKR4ejJbGn8Nl4WlWvEKaC+B"
    "CzByR2TCdOu09auI++hk0C6efTBAW6H/r4fZ/T8clQfL"
)

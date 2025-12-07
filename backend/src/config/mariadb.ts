import MariaDB from "mariadb";
import dotenv from "dotenv";

dotenv.config();

export const dbpool = MariaDB.createPool({
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT),
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  bigNumberStrings: true,
});

dbpool
  .getConnection()
  .then((conn) => {
    console.log("MariaDB connected successfully.");
    conn.release();
  })
  .catch((err) => {
    console.error("MariaDB connection failed:", err);
  });
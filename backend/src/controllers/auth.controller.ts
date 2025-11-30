import { Request, Response } from "express";
import { dbpool } from "../config/mariadb";
import bcrypt from "bcrypt";
import { v4 as uuidv4 } from "uuid";
import jwt from "jsonwebtoken";
import { User } from "../types/user.type";

class AuthController {
    // 회원가입
    static async register(req: Request, res: Response) {
        const { email, password, name } = req.body;

        // 유효성 검사
        if (!email || !password || !name) {
            return res.status(400).json({
                error: "Email, password, and name are required",
            });
        }

        // 이메일 형식 검증
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)) {
            return res.status(400).json({
                error: "Invalid email format",
            });
        }

        // 비밀번호 길이 검증
        if (password.length < 12) {
            return res.status(400).json({
                error: "Password must be at least 12 characters",
            });
        }
        const connection = await dbpool.getConnection();

        try {
            // 트랜잭션 시작
            await connection.beginTransaction();
            const check_email: User[] = await connection.query(
                "SELECT * FROM USERS WHERE email = ?",
                [email]
            )
            if (check_email.length > 0) { // length가 0이상이면 중복 email 존재
                await connection.rollback(); // 중복 이메일이 있을 경우 롤백
                return res.status(400).json({
                    error: "Email already exists",
                });
            }
            const hashedPassword = await bcrypt.hash(password, 10); // 비밀번호 해싱
            const userUuid = uuidv4(); // UUID 생성
            await connection.query(
                "INSERT INTO USERS (uuid, email, password, name) VALUES (?, ?, ?, ?)",
                [userUuid, email, hashedPassword, name]
            );
            await connection.commit();
            return res.status(201).json({
                message: "User registered successfully",
                uuid: userUuid // 회원가입 성공 시 UUID 반환(프론트에서 사용할 수도 있음)
            });
        } catch (error) {
            console.error("Register error:", error);
            await connection.rollback();
            return res.status(500).json({
                error: "Internal server error",
            });
        } finally {
            connection.release();
        }
    }
    // 로그인
    static async login(req: Request, res: Response) {
        const { email, password } = req.body;
        // email과 password가 존재하는지 확인
        if (!email || !password) {
            return res.status(400).json({
                error: "Email and password are required",
            });
        }
        try {
            const rows: User[] = await dbpool.query(
                "SELECT * FROM USERS WHERE email = ?",
                [email]
            )
            if (rows.length === 0) {
                return res.status(400).json({
                    error: "Invalid email or password",
                });
            }
            const user: User = rows[0];

            if (!user.password) {
                return res.status(400).json({
                    error: "Invalid email or password",
                });
            }

            const validPassword = await bcrypt.compare(password, user.password);
            if (!validPassword) {
                return res.status(400).json({
                    error: "Invalid email or password",
                });
            }
            const token = jwt.sign(
                { uuid: user.uuid },
                process.env.JWT_SECRET!,
                { expiresIn: "1h"}
            );

            return res.status(200).json({
                message: "Login successful",
                token: token
            });
        } catch (error) {
            return res.status(500).json({
                error: "Internal server error",
            });
        }
    }
}

export default AuthController;
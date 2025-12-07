import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

declare module "express-serve-static-core" {
  interface Request {
    user?: {
      uuid: string;
    };
  }
}

export const authMiddleware = (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    // Authorization 헤더에서 토큰 추출
    const authHeader = req.headers.authorization;
    const accessToken = authHeader && authHeader.split(" ")[1];
    if (!accessToken) {
      return res.status(401).json({
        error: "Token is missing. Please log in.",
      });
    }
    // JWT 토큰 검증 및 디코딩
    const decoded = jwt.verify(accessToken, process.env.JWT_SECRET!) as { uuid: string };
    req.user = decoded; // 사용자 정보를 요청 객체에 저장
    next(); // 다음으로 이동
  } catch (err) {
    return res.status(401).json({
      success: false,
      message: "Invalid Access Token.",
    });
  }
};
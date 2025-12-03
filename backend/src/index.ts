import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import authRouter from './routes/auth.router';
import userRouter from './routes/user.router';
import imageRouter from './routes/image.router';
import allergyRouter from './routes/allergy.router';
import dashboardRouter from './routes/dashboard.router';

dotenv.config();

const app = express();
const PORT = process.env.PORT;

// CORS 먼저
app.use(cors());

// 이미지 라우터는 body-parser 전에 등록 (multer가 처리)
app.use('/api/images', imageRouter);

// Body parser (나머지 JSON 요청용)
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// 나머지 라우터
app.use('/api/auth', authRouter);
app.use('/api/users', userRouter);
app.use('/api/allergies', allergyRouter);
app.use('/api/dashboard', dashboardRouter);

const startServer = async () => {
  try {
    app.listen(PORT, () => {
      console.log(`🚀 Server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();
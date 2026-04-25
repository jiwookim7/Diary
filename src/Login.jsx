import { useState } from 'react';
import { login } from './api/authApi.js';
import './Login.css';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await login(username, password);
      // 로그인 성공 시 localStorage에 사용자 정보 저장
      localStorage.setItem('username', response.username);
      localStorage.setItem('userId', response.user_id);
      onLoginSuccess();
    } catch (err) {
      // 에러 메시지를 더 명확하게 표시
      const errorMessage = err.message || '로그인에 실패했습니다';
      
      // 서버 연결 오류와 인증 오류 구분
      if (errorMessage.includes('서버에 연결할 수 없습니다')) {
        setError('⚠️ 서버에 연결할 수 없습니다. 서버가 시작되는 중일 수 있습니다 (최대 1분 소요). 잠시 후 다시 시도해주세요.');
      } else if (errorMessage.includes('401')) {
        setError('❌ 아이디 또는 비밀번호가 일치하지 않습니다.');
      } else {
        setError(`❌ ${errorMessage}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Welcome Back</h1>
          <p>로그인하여 일기를 작성하세요</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">사용자명</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="사용자명을 입력하세요"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            계정이 없으신가요?{' '}
            <a href="/signup" onClick={(e) => {
              e.preventDefault();
              window.location.hash = 'signup';
            }}>
              회원가입
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

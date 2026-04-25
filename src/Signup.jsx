import { useState } from 'react';
import { signup } from './api/authApi.js';
import './Login.css';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 비밀번호 확인
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }

    setIsLoading(true);

    try {
      await signup(username, password);
      // 회원가입 성공 시 로그인 페이지로 이동
      alert('회원가입이 완료되었습니다. 로그인해주세요.');
      window.location.hash = '';
    } catch (err) {
      // 에러 메시지를 더 명확하게 표시
      const errorMessage = err.message || '회원가입에 실패했습니다';
      
      // 서버 연결 오류와 중복 사용자 오류 구분
      if (errorMessage.includes('서버에 연결할 수 없습니다')) {
        setError('⚠️ 서버에 연결할 수 없습니다. 서버가 시작되는 중일 수 있습니다 (최대 1분 소요). 잠시 후 다시 시도해주세요.');
      } else if (errorMessage.includes('already exists') || errorMessage.includes('400')) {
        setError('❌ 이미 사용 중인 사용자명입니다. 다른 이름을 선택해주세요.');
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
          <h1>Create Account</h1>
          <p>새로운 계정을 만들어보세요</p>
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

          <div className="form-group">
            <label htmlFor="confirmPassword">비밀번호 확인</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="비밀번호를 다시 입력하세요"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            이미 계정이 있으신가요?{' '}
            <a href="/login" onClick={(e) => {
              e.preventDefault();
              window.location.hash = '';
            }}>
              로그인
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

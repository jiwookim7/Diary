import { apiRequest } from './client.js';

// 회원가입 API 호출
export async function signup(username, password) {
  return apiRequest('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

// 로그인 API 호출
export async function login(username, password) {
  return apiRequest('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

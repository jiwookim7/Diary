import { apiRequest } from "./client";

// 글 목록 조회
export const getPostList = async () => {
  const data = await apiRequest("/posts", { method: "GET" }); // API 요청으로 글 목록 조회
  // 안전하게 배열만 반환
  return Array.isArray(data) ? data : []; // API가 배열이 아닌 다른 형식으로 응답해도 빈 배열로 처리
};

// 회원가입 (authApi.js에서 처리하므로 제거)
// export const signup = (payload) =>
//   apiRequest("/api/signup", {
//     method: "POST",
//     body: JSON.stringify(payload),
//   });

// 로그인 (authApi.js에서 처리하므로 제거)
// export const login = (payload) =>
//   apiRequest("/api/login", {
//     method: "POST",
//     body: JSON.stringify(payload),
//   });

// 글 작성
export const createPost = (payload) =>
  apiRequest("/posts", {
    method: "POST",
    body: JSON.stringify(payload),
  });

// 글 삭제
export const deletePost = (id) =>
  apiRequest(`/posts/${id}`, {
    method: "DELETE",
  });

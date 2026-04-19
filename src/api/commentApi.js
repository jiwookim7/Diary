import { apiRequest } from './client.js';

// 특정 글의 댓글 목록 조회
export const getComments = async (postId) => {
  const data = await apiRequest(`/posts/${postId}/comments`, { method: 'GET' });
  return Array.isArray(data) ? data : [];
};

// 댓글 작성
export const createComment = async (commentData) => {
  return apiRequest('/comments', {
    method: 'POST',
    body: JSON.stringify(commentData),
  });
};

// 댓글 삭제
export const deleteComment = async (commentId) => {
  return apiRequest(`/comments/${commentId}`, {
    method: 'DELETE',
  });
};

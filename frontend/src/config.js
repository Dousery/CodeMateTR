// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

// Helper function for audio URLs
export const getAudioUrl = (audioPath) => {
  return `${API_BASE_URL}${audioPath}`;
};

export const API_ENDPOINTS = {
  // Base URL
  BASE_URL: API_BASE_URL,
  
  // Auth endpoints
  LOGIN: `${API_BASE_URL}/login`,
  REGISTER: `${API_BASE_URL}/register`,
  LOGOUT: `${API_BASE_URL}/logout`,
  PROFILE: `${API_BASE_URL}/profile`,
  CHANGE_PASSWORD: `${API_BASE_URL}/change_password`,
  SET_INTEREST: `${API_BASE_URL}/set_interest`,
  SET_API_KEY: `${API_BASE_URL}/set_api_key`,
  SESSION_STATUS: `${API_BASE_URL}/session-status`,
  HEALTH: `${API_BASE_URL}/health`,

  // Test endpoints
  TEST_PAGE: `${API_BASE_URL}/test`,
  TEST_SKILL: `${API_BASE_URL}/test_your_skill`,
  TEST_EVALUATE: `${API_BASE_URL}/test_your_skill/evaluate`,
  TEST_STATISTICS: `${API_BASE_URL}/test_your_skill/statistics`,
  TEST_REFRESH_POOL: `${API_BASE_URL}/test_your_skill/refresh_pool`,
  TEST_RECOMMEND_ADAPTIVE: `${API_BASE_URL}/test_your_skill/recommend_adaptive`,

  // Code endpoints
  CODE_PAGE: `${API_BASE_URL}/code`,

  // Auto Interview endpoints
  AUTO_INTERVIEW_PAGE: `${API_BASE_URL}/auto-interview`,



  // Interview endpoints
  INTERVIEW_SIMULATION: `${API_BASE_URL}/interview_simulation`,
  INTERVIEW_EVALUATE: `${API_BASE_URL}/interview_simulation/evaluate`,
  INTERVIEW_SPEECH_QUESTION: `${API_BASE_URL}/interview_speech_question`,
  INTERVIEW_SPEECH_EVALUATION: `${API_BASE_URL}/interview_speech_evaluation`,
  INTERVIEW_CV_QUESTION: `${API_BASE_URL}/interview_cv_based_question`,
  INTERVIEW_CV_SPEECH_QUESTION: `${API_BASE_URL}/interview_cv_speech_question`,
  INTERVIEW_PERSONALIZED: `${API_BASE_URL}/interview_personalized_questions`,
  UPLOAD_CV: `${API_BASE_URL}/upload_cv`,

  // Auto Interview endpoints
  AUTO_INTERVIEW_START: `${API_BASE_URL}/auto_interview/start`,
  AUTO_INTERVIEW_SUBMIT: `${API_BASE_URL}/auto_interview/submit_answer`,
  AUTO_INTERVIEW_COMPLETE: `${API_BASE_URL}/auto_interview/complete`,
  AUTO_INTERVIEW_STATUS: `${API_BASE_URL}/auto_interview/status`,

  // Code endpoints
  CODE_ROOM: `${API_BASE_URL}/code_room`,
  CODE_EVALUATE: `${API_BASE_URL}/code_room/evaluate`,
  CODE_RUN: `${API_BASE_URL}/code_room/run`,
  CODE_RUN_SIMPLE: `${API_BASE_URL}/code_room/run_simple`,
  CODE_GENERATE: `${API_BASE_URL}/code_room/generate_solution`,
  CODE_SUGGEST: `${API_BASE_URL}/code_room/suggest_resources`,
  CODE_FORMAT: `${API_BASE_URL}/code_room/format_code`,

  // Forum endpoints
  FORUM_POSTS: `${API_BASE_URL}/forum/posts`,
  FORUM_STATS: `${API_BASE_URL}/forum/stats`,
  FORUM_LEADERBOARD: `${API_BASE_URL}/forum/leaderboard`,
  FORUM_NOTIFICATIONS: `${API_BASE_URL}/forum/notifications`,
  FORUM_NOTIFICATIONS_MARK_READ: `${API_BASE_URL}/forum/notifications/mark-read`,
  FORUM_REPORT: `${API_BASE_URL}/forum/report`,

  // Admin endpoints
  ADMIN_SEND_NOTIFICATION: `${API_BASE_URL}/admin/send-notification`,
  ADMIN_FORUM_POSTS: `${API_BASE_URL}/admin/forum/posts`,
  ADMIN_FORUM_PERMANENT_DELETE: `${API_BASE_URL}/admin/forum/posts`,
  ADMIN_USERS: `${API_BASE_URL}/admin/users`,
  ADMIN_STATS: `${API_BASE_URL}/admin/stats`,



  // Debug endpoints
  DEBUG_CLEAR_SESSIONS: `${API_BASE_URL}/debug/clear_auto_interview_sessions`,
};

export default API_ENDPOINTS;

// Debug için console.log ekle
console.log('API_ENDPOINTS loaded:', API_ENDPOINTS); 
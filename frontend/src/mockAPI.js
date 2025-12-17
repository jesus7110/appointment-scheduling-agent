// Deprecated mock API. Frontend now calls the real backend.
export const getBotResponse = async () => {
  throw new Error("Mock API disabled. Use real backend /api/chat.");
};

export const resetMockAPI = () => {};


import apiClient from "@/lib/api-client";
import { User, LoginCredentials, RegisterData, LoginResponse } from "@/types";

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return apiClient.login(credentials.email, credentials.password);
  }

  async register(data: RegisterData) {
    return apiClient.register(data);
  }

  async getProfile(): Promise<User> {
    return apiClient.get<User>("/api/auth/profile/");
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return apiClient.patch<User>("/api/auth/profile/", data);
  }

  async logout() {
    return apiClient.logout();
  }

  // Features to implement later if needed
  async changePassword(data: { current_password: string; new_password: string }) {
    return apiClient.post("/api/auth/change-password/", {
      old_password: data.current_password,
      new_password: data.new_password
    });
  }

  async requestPasswordReset(email: string) {
    return apiClient.post("/api/auth/password-reset/", { email });
  }

  async deleteAccount(data: { password: string; confirmation: string }) {
    return apiClient.post("/api/auth/delete-account/", data);
  }
}

export const authService = new AuthService();
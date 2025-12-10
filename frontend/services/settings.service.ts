/**
 * User Settings Service - API integration for user preferences
 */

import apiClient from "@/lib/api-client";
import { UserSettings } from "@/types/banking";

class SettingsService {
  async getSettings(): Promise<UserSettings> {
    return apiClient.get<UserSettings>("/api/auth/settings/");
  }

  async updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
    return apiClient.patch<UserSettings>("/api/auth/settings/", data);
  }
}

export const settingsService = new SettingsService();

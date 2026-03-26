"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Load current values from user
  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
      setPhone(user.phone || "");
    }
  }, [user]);

  const handleProfileSave = useCallback(async () => {
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      await api.updateProfile({
        name: name || undefined,
        email: email || undefined,
        phone: phone || undefined,
      });
      await refreshUser();
      setSuccess("Profile updated successfully.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }, [name, email, phone, refreshUser]);

  const handlePasswordSave = useCallback(async () => {
    setError("");
    setSuccess("");

    if (!currentPassword) {
      setError("Current password is required.");
      return;
    }
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }

    setSaving(true);
    try {
      await api.updateProfile({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSuccess("Password changed successfully.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to change password");
    } finally {
      setSaving(false);
    }
  }, [currentPassword, newPassword, confirmPassword]);

  if (!user) {
    return <div className="animate-pulse text-gray-400">Loading...</div>;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>

      {/* Feedback */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
          {success}
        </div>
      )}

      {/* Profile Section */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
        <div className="space-y-4">
          <Field label="Full Name" value={name} onChange={setName} placeholder="Your name" />
          <Field label="Email" value={email} onChange={setEmail} placeholder="you@example.com" type="email" />
          <Field label="Phone" value={phone} onChange={setPhone} placeholder="(555) 123-4567" type="tel" />

          <div className="flex items-center gap-3 pt-2">
            <span className="text-sm text-gray-500">
              Role: <span className="font-medium text-gray-700 capitalize">{user.role}</span>
            </span>
          </div>

          <button
            onClick={handleProfileSave}
            disabled={saving}
            className={cn(
              "rounded-lg px-5 py-2.5 text-sm font-medium text-white transition-colors",
              saving
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-solar-600 hover:bg-solar-700"
            )}
          >
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </div>
      </div>

      {/* Password Section */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h2>
        <div className="space-y-4">
          <Field
            label="Current Password"
            value={currentPassword}
            onChange={setCurrentPassword}
            type="password"
            placeholder="Enter current password"
          />
          <Field
            label="New Password"
            value={newPassword}
            onChange={setNewPassword}
            type="password"
            placeholder="At least 8 characters"
          />
          <Field
            label="Confirm New Password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            type="password"
            placeholder="Re-enter new password"
          />

          <button
            onClick={handlePasswordSave}
            disabled={saving || !currentPassword || !newPassword}
            className={cn(
              "rounded-lg px-5 py-2.5 text-sm font-medium text-white transition-colors",
              saving || !currentPassword || !newPassword
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-solar-600 hover:bg-solar-700"
            )}
          >
            {saving ? "Changing..." : "Change Password"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-solar-500 focus:ring-1 focus:ring-solar-500 outline-none"
      />
    </div>
  );
}

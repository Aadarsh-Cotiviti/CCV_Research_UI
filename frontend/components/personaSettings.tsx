"use client";

import { useProfileStore } from "./authComponents";
import { useState } from "react";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { UserRole } from "@/db/schemas";

interface PersonaSettingsProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

const roleDisplayNames: Record<UserRole, string> = {
  analyst: "Analyst",
  sme: "Subject Matter Expert (SME)",
  "data-analyst": "Data Analyst",
  "clinical-reviewer": "Clinical Reviewer",
  "audit-lead": "Audit Lead",
  "it-engineer": "IT/Engineer",
  other: "Other",
};

const roleDescriptions: Record<UserRole, string> = {
  analyst: "General business analyst focused on process improvement and data insights",
  sme: "Subject matter expert with deep domain knowledge in specific areas",
  "data-analyst": "Specialist in data analysis, reporting, and statistical modeling",
  "clinical-reviewer": "Healthcare professional reviewing clinical data and protocols",
  "audit-lead": "Lead auditor responsible for compliance and risk assessment",
  "it-engineer": "Technical professional handling system architecture and engineering",
  other: "Other role not specified above",
};

export const PersonaSettings = ({ isOpen, onOpenChange }: PersonaSettingsProps) => {
  const userProfile = useProfileStore((store) => store.userProfile);
  const updateUserRole = useProfileStore((store) => store.updateUserRole);
  const loading = useProfileStore((store) => store.loading);

  const [selectedRole, setSelectedRole] = useState<UserRole>(userProfile?.role || "other");

  const handleSave = async () => {
    if (selectedRole !== userProfile?.role) {
      await updateUserRole(selectedRole);
    }
    onOpenChange(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>AI Assistant Persona Settings</DialogTitle>
          <DialogDescription>
            Choose your role to help the AI assistant provide more targeted responses and
            suggestions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label htmlFor="role-select" className="text-sm font-medium">
              Your Role
            </label>
            <Select
              value={selectedRole}
              onValueChange={(value) => setSelectedRole(value as UserRole)}
            >
              <SelectTrigger id="role-select">
                <SelectValue placeholder="Select your role" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(roleDisplayNames).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedRole && (
              <p className="text-sm text-muted-foreground">{roleDescriptions[selectedRole]}</p>
            )}
          </div>

          <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
            <strong>How this helps:</strong> The AI assistant will tailor its responses based on
            your role, providing relevant examples, terminology, and recommendations specific to
            your work area.
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || selectedRole === userProfile?.role}>
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

import { apiClient } from "./client";

export const getFindings = async () => {
  const { data } = await apiClient.get("/artifacts/findings");
  return data;
};

export const getSources = async () => {
  const { data } = await apiClient.get("/artifacts/sources");
  return data;
};

export const getEvidence = async () => {
  const { data } = await apiClient.get("/artifacts/evidence");
  return data;
};

export const getPolicy = async () => {
  const { data } = await apiClient.get("/artifacts/policy");
  return data;
};

export const getRepair = async () => {
  const { data } = await apiClient.get("/artifacts/repair");
  return data;
};

export const getVerification = async () => {
  const { data } = await apiClient.get("/artifacts/verification");
  return data;
};

export const listDemoRepos = async () => {
  const { data } = await apiClient.get("/demo/repos");
  return data;
};

export const loadDemo = async (repoName: string) => {
  const { data } = await apiClient.post(`/demo/load/${repoName}`);
  return data;
};

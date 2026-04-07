import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/auth",
});

// Attach token automatically
API.interceptors.request.use((req) => {
  const token = localStorage.getItem("token");
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

// AUTH
export const studentSignup = (data) => API.post("/signup", data);
export const userLogin = (data) => API.post("/login", data);

// ADMIN
export const createUserByAdmin = (data) =>
  API.post("/admin/pre_create_users", data);

export const getAllUsers = () =>
  API.get("/admin/users_view_edit");

export const deleteUser = (id) =>
  API.delete(`/admin/${id}/delete`);


// Import the functions you need from the SDKs
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyARPxw08Xs4uA3hxr88kWAQA0VFDnt2q7k",
  authDomain: "codecogni-4de99.firebaseapp.com",
  projectId: "codecogni-4de99",
  storageBucket: "codecogni-4de99.firebasestorage.app",
  messagingSenderId: "1058295623408",
  appId: "1:1058295623408:web:8a0e019146b97f830b5c35",
  measurementId: "G-Q0Z124YRJC",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Analytics only on client side to prevent SSR issues
let analytics = null;
if (typeof window !== "undefined") {
  analytics = getAnalytics(app);
}

// Initialize Google Auth Provider
const googleProvider = new GoogleAuthProvider();

// ✅ Export auth and providers to use in Login & Register
export const auth = getAuth(app);
export { analytics, googleProvider };
export default app;

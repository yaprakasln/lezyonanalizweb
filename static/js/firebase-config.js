// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIZaSyDoLZbZYLRORYLxNAGCnvxAaTeuWqEGeMA",
  authDomain: "dermaai-7c567.firebaseapp.com",
  databaseURL: "https://dermaai-7c567-default-rtdb.firebaseio.com",
  projectId: "dermaai-7c567",
  storageBucket: "dermaai-7c567.firebasestorage.app",
  messagingSenderId: "510294818267",
  appId: "1:510294818267:web:60897e9413a7674adbfbfe",
  measurementId: "G-WCWMLFVF73"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export { app, analytics }; 
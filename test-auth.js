import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.VITE_SUPABASE_URL || "https://boepdarunbvfpxhcjsef.supabase.co";
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testAuth() {
  console.log("Testing Supabase Auth Configuration...");
  
  const email = `test_hackathon_${Date.now()}@example.com`;
  const password = "SecurePassword123!";
  
  console.log(`\n1. Signing up with ${email}...`);
  const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: "Hackathon Test",
        company: "Test Co"
      }
    }
  });
  
  if (signUpError) {
    console.error("Sign Up Failed:", signUpError.message);
    return;
  }
  
  console.log("Sign Up Success!");
  console.log("Has Session immediately? ", !!signUpData.session);
  console.log("Is Email Confirmed? ", !!signUpData.user?.email_confirmed_at);
  
  if (!signUpData.session) {
    console.log("Email confirmation is likely ENABLED. We did not get a session.");
  } else {
    console.log("Email confirmation is likely DISABLED. Session obtained.");
  }
  
  // Try to sign in
  console.log(`\n2. Signing in with ${email}...`);
  const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
    email,
    password
  });
  
  if (signInError) {
    console.error("Sign In Failed:", signInError.message);
  } else {
    console.log("Sign In Success!");
    console.log("User Object:");
    console.log(JSON.stringify(signInData.user, null, 2));
  }
}

testAuth();

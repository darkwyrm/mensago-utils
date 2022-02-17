use argon2::{self, Config, ThreadMode, Variant, Version};
use rand::Rng;
use stopwatch::{Stopwatch};

fn hash_password(password: &str) {
	let salt = rand::thread_rng().gen::<[u8; 16]>();
	
	let config = Config {
		variant: Variant::Argon2id,
		version: Version::Version13,
		mem_cost: 65536,
		time_cost: 1,
		lanes: 2,
		thread_mode: ThreadMode::Parallel,
		secret: &[],
		ad: &[],
		hash_length: 32
	};
	let sw = Stopwatch::start_new();
	let hash = argon2::hash_encoded(password.as_bytes(), &salt, &config).unwrap();
	println!("The hash is {} and took {}ms to generate", hash, sw.elapsed_ms());
}

fn main() {
	hash_password("MySecretPassword");
}

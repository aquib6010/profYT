import { Container } from "../../ui/Container";
import { ButtonLink } from "../../ui/Button";
import { loginUrl } from "../../auth/useAuth";

export function CTASection() {
  return (
    <section className="py-20 sm:py-28">
      <Container>
        <div className="overflow-hidden rounded-2xl bg-ink px-8 py-16 text-center sm:px-16">
          <h2 className="mx-auto max-w-2xl text-display-md font-bold text-paper sm:text-display-lg">
            See which videos actually paid you.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-paper/70">
            Connect your channel in under a minute. Read-only, encrypted, free to start.
          </p>
          <div className="mt-8 flex justify-center">
            <ButtonLink href={loginUrl} size="lg">
              Connect your YouTube channel
            </ButtonLink>
          </div>
        </div>
      </Container>
    </section>
  );
}

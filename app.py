"""Taylor-Couette flow visualizer: velocity profile between concentric rotating cylinders."""
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Taylor-Couette Flow Visualizer", layout="wide")

# ---------------- Physics ----------------
def couette_coeffs(R1, R2, w1, w2):
    """Return A, B for v_theta(r) = A*r + B/r."""
    denom = R2**2 - R1**2
    A = (w2 * R2**2 - w1 * R1**2) / denom
    B = (w1 - w2) * R1**2 * R2**2 / denom
    return A, B

def v_theta(r, A, B):
    return A * r + B / r

def omega(r, A, B):
    return A + B / r**2

# ---------------- Sidebar ----------------
st.sidebar.header("Geometry & Rotation")
R1 = st.sidebar.slider("Inner radius R1", 0.1, 2.0, 1.0, 0.05)
R2 = st.sidebar.slider("Outer radius R2", 0.5, 3.0, 2.0, 0.05)
if R2 <= R1:
    st.sidebar.error("R2 must be larger than R1")
    st.stop()
w1 = st.sidebar.slider("Inner angular velocity ω1 (rad/s)", -5.0, 5.0, 2.0, 0.1)
w2 = st.sidebar.slider("Outer angular velocity ω2 (rad/s)", -5.0, 5.0, 0.5, 0.1)
n_vec = st.sidebar.slider("Vector field density", 10, 30, 18, 1)
show_stream = st.sidebar.checkbox("Overlay streamlines", value=True)

A, B = couette_coeffs(R1, R2, w1, w2)

st.title("Taylor–Couette Flow: Velocity Between Concentric Cylinders")
st.markdown(
    "Laminar azimuthal flow in the gap between two independently rotating cylinders. "
    "Use the sidebar to spin the cylinders and watch the profile respond."
)

tab_vis, tab_theory = st.tabs(["Visualization", "Theory: derivation without Navier–Stokes"])

with tab_vis:
    col1, col2 = st.columns(2)

    r = np.linspace(R1, R2, 300)
    v = v_theta(r, A, B)
    om = omega(r, A, B)

    with col1:
        st.subheader("Velocity profile vθ(r)")
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        ax1.plot(r, v, lw=2.5)
        ax1.axvline(R1, color="gray", ls="--", alpha=0.6)
        ax1.axvline(R2, color="gray", ls="--", alpha=0.6)
        ax1.set_xlabel("r")
        ax1.set_ylabel("vθ(r)")
        ax1.set_title("Azimuthal velocity across the gap")
        ax1.grid(alpha=0.3)
        st.pyplot(fig1)

        st.latex(r"v_\theta(r) = A r + \frac{B}{r}")
        st.latex(
            r"A = \frac{\omega_2 R_2^2 - \omega_1 R_1^2}{R_2^2 - R_1^2}"
            r",\quad B = \frac{(\omega_1 - \omega_2) R_1^2 R_2^2}{R_2^2 - R_1^2}"
        )
        st.write(f"Current values: A = {A:.3f}, B = {B:.3f}")

    with col2:
        st.subheader("Angular velocity Ω(r)")
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.plot(r, om, lw=2.5, color="darkorange")
        ax2.axvline(R1, color="gray", ls="--", alpha=0.6)
        ax2.axvline(R2, color="gray", ls="--", alpha=0.6)
        ax2.set_xlabel("r")
        ax2.set_ylabel("Ω(r) = vθ/r")
        ax2.set_title("Angular velocity across the gap")
        ax2.grid(alpha=0.3)
        st.pyplot(fig2)

    st.subheader("Cross-section vector field (r–θ plane)")
    st.markdown(
        "Arrows show the local fluid velocity. Their length is proportional to speed; "
        "color also encodes speed."
    )
    # Vector field on a Cartesian grid, masked to the annulus
    n = n_vec
    x = np.linspace(-R2 * 1.1, R2 * 1.1, n)
    y = np.linspace(-R2 * 1.1, R2 * 1.1, n)
    X, Y = np.meshgrid(x, y)
    Rs = np.sqrt(X**2 + Y**2)
    mask = (Rs >= R1) & (Rs <= R2)
    Theta = np.arctan2(Y, X)
    Vt = np.full_like(Rs, np.nan)
    Vt[mask] = v_theta(Rs[mask], A, B)
    Vx = np.full_like(Rs, np.nan)
    Vy = np.full_like(Rs, np.nan)
    Vx[mask] = -Vt[mask] * np.sin(Theta[mask])
    Vy[mask] = Vt[mask] * np.cos(Theta[mask])
    speed = np.sqrt(Vx**2 + Vy**2)

    fig3, ax3 = plt.subplots(figsize=(7, 7))
    # draw cylinder walls
    th = np.linspace(0, 2 * np.pi, 200)
    ax3.plot(R1 * np.cos(th), R1 * np.sin(th), "k-", lw=3, label="Inner wall")
    ax3.plot(R2 * np.cos(th), R2 * np.sin(th), "k-", lw=3, label="Outer wall")
    q = ax3.quiver(
        X, Y, Vx, Vy, speed,
        cmap="viridis", scale=None, width=0.012, pivot="mid",
    )
    if show_stream:
        # streamlines on a finer polar grid converted to cartesian
        r_s = np.linspace(R1, R2, 40)
        th_s = np.linspace(0, 2 * np.pi, 120)
        Rg, Tg = np.meshgrid(r_s, th_s)
        Vs = v_theta(Rg, A, B)
        Us = -Vs * np.sin(Tg)
        Ws = Vs * np.cos(Tg)
        Xs = Rg * np.cos(Tg)
        Ys = Rg * np.sin(Tg)
        ax3.streamplot(
            Xs, Ys, Us, Ws, color="white", linewidth=0.7,
            arrowsize=0.8, density=1.2, broken_streamlines=False,
        )
    ax3.set_aspect("equal")
    ax3.set_xlim(-R2 * 1.15, R2 * 1.15)
    ax3.set_ylim(-R2 * 1.15, R2 * 1.15)
    ax3.set_xlabel("x")
    ax3.set_ylabel("y")
    ax3.set_title("Velocity vectors in the annulus")
    fig3.colorbar(q, ax=ax3, label="speed |v|")
    ax3.legend(loc="upper right")
    st.pyplot(fig3)

with tab_theory:
    st.header("Theory: the profile from symmetry, torque balance, and geometry")
    st.markdown(
        "_No Navier–Stokes equations are invoked. Everything follows from_ "
        "_symmetry, the no-slip condition, steady angular-momentum balance, "
        "_and a geometric picture of shear between curved layers._"
    )

    st.subheader("1. What the flow must look like (symmetry)")
    st.markdown(
        "The setup is invariant under rotations about the axis and translations along it. "
        "In a steady laminar state we expect the same symmetries in the flow: no dependence "
        "on angle θ or height z, no radial or axial motion (nothing drives fluid inward or "
        "upward), so the velocity is purely azimuthal and a function of radius alone:"
    )
    st.latex(r"\mathbf{v} = v_\theta(r)\,\hat{\boldsymbol{\theta}}, \qquad \Omega(r) \equiv \frac{v_\theta(r)}{r}")

    st.subheader("2. No-slip at the walls")
    st.markdown(
        "Fluid in contact with a solid wall moves with the wall. The walls are the two "
        "cylinder surfaces, so:"
    )
    st.latex(r"v_\theta(R_1) = \omega_1 R_1, \qquad v_\theta(R_2) = \omega_2 R_2")

    st.subheader("3. Torque on any cylindrical shell is the same (steady angular momentum)")
    st.markdown(
        "Picture a thin cylindrical shell of fluid at radius r, of length L. Its angular "
        "momentum can only change if there is a net torque on it. In steady flow the angular "
        "momentum of every shell is constant, and there are no body torques — so the torque "
        "exerted by the fluid inside r on the shell must exactly balance the torque exerted "
        "by the fluid outside r. Hence the torque transmitted across _every_ cylindrical "
        "surface is the same constant T."
    )
    st.latex(r"T(r) = T = \text{constant (independent of } r\text{)}")
    st.markdown(
        "Torque = (tangential shear force) × (lever arm). On a cylinder of radius r and "
        "length L, area = 2πrL, shear stress = τ(r), lever arm = r:"
    )
    st.latex(r"T = \tau(r)\,(2\pi r L)\,r = 2\pi L\,r^2\,\tau(r) = \text{const}")

    st.subheader("4. Shear rate from geometry: neighboring rings slide by r·dΩ/dr")
    st.markdown(
        "Consider two nearby rings at r and r + dr, rotating at Ω(r) and Ω(r + dr). "
        "In a short time dt, the outer ring advances by an extra angle dΩ·dt relative to "
        "the inner ring. A small fluid element spanning the gap gets tilted: the tangential "
        "displacement difference across dr is r·dΩ·dt. Dividing by dr·dt gives the rate of "
        "angular shear strain:"
    )
    st.latex(r"\dot{\gamma}(r) = r\,\frac{d\Omega}{dr}")
    st.markdown(
        "Physical check: if the whole fluid rotates as a solid body (Ω = const), there is no "
        "sliding between rings and the shear is zero — the formula gives exactly that. "
        "For a Newtonian fluid, shear stress is proportional to shear rate, τ = μ·γ̇, so:"
    )
    st.latex(r"\tau(r) = \mu\, r\,\frac{d\Omega}{dr}")

    st.subheader("5. Constant torque → a simple differential equation")
    st.markdown("Insert the shear stress into the torque expression:")
    st.latex(r"T = 2\pi L\,r^2 \left(\mu\, r\,\frac{d\Omega}{dr}\right) = 2\pi\mu L\,r^3\frac{d\Omega}{dr}")
    st.markdown("Since T is constant, so is the combination r³·dΩ/dr:")
    st.latex(r"r^3\,\frac{d\Omega}{dr} = C \quad (\text{constant})")
    st.markdown("This is the whole dynamics in one line — no PDEs needed. Integrate:")
    st.latex(r"\frac{d\Omega}{dr} = \frac{C}{r^3} \;\;\Longrightarrow\;\; \Omega(r) = A - \frac{C}{2r^2}")
    st.markdown("Multiply by r to get the linear velocity, and rename the constant:")
    st.latex(r"\boxed{\,v_\theta(r) = A\,r + \frac{B}{r}\,}")
    st.markdown(
        "Geometric reading: the **Ar** term is solid-body rotation (rings moving together, "
        "no shear); the **B/r** term is a potential-vortex swirl (fast near the center, "
        "required whenever the cylinders rotate at different rates, because torque must "
        "still be transmitted uniformly)."
    )

    st.subheader("6. Fix A and B from the walls")
    st.markdown("Apply the no-slip conditions:")
    st.latex(r"\begin{cases} A R_1 + B/R_1 = \omega_1 R_1 \\ A R_2 + B/R_2 = \omega_2 R_2 \end{cases}")
    st.markdown("Solving the two linear equations:")
    st.latex(
        r"\boxed{\,A = \frac{\omega_2 R_2^2 - \omega_1 R_1^2}{R_2^2 - R_1^2}\,},"
        r"\qquad \boxed{\,B = \frac{(\omega_1 - \omega_2)\,R_1^2 R_2^2}{R_2^2 - R_1^2}\,}"
    )

    st.subheader("7. Sanity checks (purely physical)")
    st.markdown(
        "- **Both cylinders spin together** (ω₁ = ω₂ = ω): then B = 0 and A = ω, so "
        "v_θ = ωr — solid-body rotation, zero shear, as expected.\n"
        "- **Narrow gap** (R₂ − R₁ ≪ R₁): expand the profile and it becomes nearly linear "
        "across the gap — locally it looks like simple shear between parallel plates.\n"
        "- **Outer cylinder at rest, inner spinning**: B ≠ 0 gives the characteristic "
        "1/r decay of a vortex, steepest near the inner wall where the shear is largest.\n"
        "- **Torque**: T = −4πμL·B, so the constant B directly measures the torque "
        "transmitted through the fluid — one number, same at every radius."
    )
    st.latex(r"T = -4\pi\,\mu\,L\,B")

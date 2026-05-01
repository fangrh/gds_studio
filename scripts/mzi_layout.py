"""Example GDS layout: Mach-Zehnder Interferometer with photonic components."""
import gdsfactory as gf

c = gf.Component("mzi_layout")

# MZI interferometer
mzi = gf.components.mzi(delta_length=10, length_x=50)
mzi_ref = c << mzi

# Ring resonator
ring = gf.components.ring_single(radius=10, gap=0.3)
ring_ref = c << ring
ring_ref.move((300, -80))

# Spiral delay line
spiral = gf.components.spiral(length=500)
spiral_ref = c << spiral
spiral_ref.move((-200, -200))

# Coupler
coupler = gf.components.coupler_straight(length=20, gap=0.3)
coupler_ref = c << coupler
coupler_ref.move((-100, -150))

# Labels
c.add_label(text="MZI Layout Demo", position=(0, 150), layer="TEXT")
c.add_label(text="Ring Resonator", position=(300, -110), layer="TEXT")
c.add_label(text="Spiral Delay", position=(-200, -280), layer="TEXT")

c.write_gds("gds/mzi_layout.gds")
print(f"Written: gds/mzi_layout.gds")
